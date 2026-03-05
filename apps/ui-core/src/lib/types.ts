// TypeScript Type Definitions for Svelte Frontend

export interface Category {
  id: string;
  name: string;
  slug: string;
  parentId: string | null;
  productCount: number;
  children: Category[];
  createdAt: string;
}

export interface User {
  id: string;
  email: string;
  name: string | null;
  status: string;
  roles: Role[];
  createdAt: string;
}

export interface Role {
  id: string;
  name: string;
  code: string;
  description: string | null;
  permissions: Permission[];
}

export interface Permission {
  id: string;
  name: string;
  code: string;
  description: string | null;
}

export interface Order {
  id: string;
  customerName: string;
  status: string;
  total: number;
  items: number;
  createdAt: string;
}

export interface Article {
  id: string;
  title: string;
  slug: string;
  excerpt: string | null;
  status: string;
  category: string;
  views: number;
  author: string;
  authorId: string | null;
  createdAt: string;
}

export interface Product {
    id: string;
    name: string;
    sku: string;
    price: number;
    stock: number;
    status: string;
    category: string;
    categoryId: string | null;
    description: string | null;
    type: string;
    createdAt: string;
}
