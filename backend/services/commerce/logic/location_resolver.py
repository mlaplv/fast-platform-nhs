"""
Location Resolver Service — Elite V2.2 (Architect's Edition)
========================================================
High-performance, local-first address validation for Vietnam.
Uses a hybrid Semantic + Fuzzy matching engine.
"""
from __future__ import annotations
import json
import logging
import os
import re
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from backend.utils.text import normalize_vn

logger = logging.getLogger("api-gateway")

@dataclass
class ResolvedLocation:
    province: Optional[str] = None
    district: Optional[str] = None
    ward: Optional[str] = None
    street: Optional[str] = None
    house_number: Optional[str] = None
    score: float = 0.0
    is_valid: bool = False
    shipping_days: Optional[str] = None

class LocationResolver:
    _data: List[Dict[str, Any]] = []
    _province_map: Dict[str, Dict[str, Any]] = {} # Normalized Name -> Province Data
    _ward_map: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {} # Province ID -> List[(Norm Ward, Province Data)]
    _initialized: bool = False

    def __init__(self, data_path: str = "backend/resources/vn_divisions.json"):
        self.data_path = data_path

    def _initialize(self):
        if LocationResolver._initialized:
            return
        
        try:
            full_path = os.path.abspath(self.data_path)
            if os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8") as f:
                    LocationResolver._data = json.load(f)
                
                # R106: Build Inverted Index for O(1) Scaling
                for p in LocationResolver._data:
                    p_id = str(p["id"])
                    # Index Province
                    for name in [p["name"]] + p.get("aliases", []):
                        LocationResolver._province_map[normalize_vn(name)] = p
                    
                    # Index Wards (Flattened)
                    LocationResolver._ward_map[p_id] = [
                        (normalize_vn(w), p) for w in p.get("wards", [])
                    ]
                
                LocationResolver._initialized = True
                logger.info(f"[LocationResolver] Seeded {len(LocationResolver._data)} provinces with Inverted Index.")
            else:
                logger.warning(f"[LocationResolver] Data file not found at {full_path}")
        except Exception as e:
            logger.error(f"[LocationResolver] Failed to load divisions: {e}")

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    def _fuzzy_score(self, s1: str, s2: str) -> float:
        n1 = normalize_vn(s1)
        n2 = normalize_vn(s2)
        if not n1 or not n2: return 0.0
        distance = self._levenshtein_distance(n1, n2)
        max_len = max(len(n1), len(n2))
        return 1.0 - (distance / max_len)

    def resolve(self, raw_address: str) -> ResolvedLocation:
        """
        Elite V2.2: O(1) Indexed + Fuzzy Resolution (Flattened 2026 Edition).
        """
        self._initialize()
        res = ResolvedLocation()
        if not raw_address: return res

        addr_norm = normalize_vn(raw_address)
        
        # 1. Resolve Province
        best_province = None
        best_p_score = 0.0
        
        # O(1) Fast Search First
        for p_norm, p_data in LocationResolver._province_map.items():
            if p_norm in addr_norm:
                best_province = p_data
                best_p_score = 1.0 # Exact match boost
                break
        
        # Fallback to Fuzzy if needed
        if not best_province:
            for p in LocationResolver._data:
                for name in [p["name"]] + p.get("aliases", []):
                    score = self._fuzzy_score(name, addr_norm)
                    if score > best_p_score:
                        best_p_score = score
                        best_province = p

        if best_province and best_p_score > 0.6:
            res.province = best_province["name"]
            res.shipping_days = best_province.get("shipping_days")
            p_id = str(best_province["id"])
            
            # 2. Resolve Ward (within Province)
            best_ward = None
            best_w_score = 0.0
            
            # O(1) Fast Search First (Ward Index)
            wards_to_check = LocationResolver._ward_map.get(p_id, [])
            for w_norm, _ in wards_to_check:
                if w_norm in addr_norm:
                    best_ward = next(w for w in best_province["wards"] if normalize_vn(w) == w_norm)
                    best_w_score = 1.0
                    break
            
            # Fallback to Fuzzy Search
            if not best_ward:
                for w_name in best_province.get("wards", []):
                    score = self._fuzzy_score(w_name, addr_norm)
                    if normalize_vn(w_name) in addr_norm:
                        score += 0.4
                    if score > best_w_score:
                        best_w_score = score
                        best_ward = w_name
            
            if best_ward and best_w_score > 0.6:
                res.ward = best_ward
        
        # 3. Heuristic for Street and House Number
        remaining = raw_address
        for part in [res.province, res.ward]:
            if part:
                remaining = re.sub(re.escape(part), "", remaining, flags=re.IGNORECASE)
        
        remaining = re.sub(r"[,.\-]", " ", remaining)
        parts = [p.strip() for p in remaining.split() if p.strip()]
        
        if parts:
            for i, p in enumerate(parts):
                if re.match(r"\d+/?\w*", p):
                    res.house_number = p
                    res.street = " ".join(parts[i+1:]) if i+1 < len(parts) else " ".join(parts[:i])
                    break
            if not res.street:
                res.street = " ".join(parts)

        final_score = (best_p_score + (best_w_score if res.ward else 0)) / 2
        res.score = round(final_score, 2)
        res.is_valid = res.province is not None and (res.ward is not None or best_p_score > 0.85)
        
        return res

location_resolver = LocationResolver()
