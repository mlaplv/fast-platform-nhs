import logging
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from litestar import Controller, get, post, patch, delete, Request
from litestar.di import Provide
from litestar.exceptions import NotFoundException
from advanced_alchemy.filters import FilterTypes

from backend.database.models import Appointment
from backend.database.repositories import AppointmentRepository, provide_appointment_repo
from backend.schemas.scheduler import (
    AppointmentCreate, 
    AppointmentUpdate, 
    AppointmentResponse,
    AppointmentListResponse
)

from backend.constants.permissions import PermissionEnum
from backend.guards import PermissionGuard

logger = logging.getLogger("api-gateway")

class SchedulerController(Controller):
    path = "/api/v1/appointments"
    guards = [PermissionGuard(PermissionEnum.SCHEDULE_READ)]
    dependencies = {"appointment_repo": Provide(provide_appointment_repo)}

    @get("/")
    async def list_appointments(
        self, 
        appointment_repo: AppointmentRepository,
        limit: int = 100,
        offset: int = 0
    ) -> AppointmentListResponse:
        """Thưa Sếp, đây là danh sách các phiên làm việc Neural đã được lên lịch."""
        from sqlalchemy import select, func
        
        try:
            # R102 Professional Upgrade: Direct safe query to bypass repository windowing bug
            stmt = select(Appointment).order_by(Appointment.start_time).limit(limit).offset(offset)
            result = await appointment_repo.session.execute(stmt)
            appointments = result.scalars().all()
            
            # Count separately for total
            count_stmt = select(func.count()).select_from(Appointment)
            count_result = await appointment_repo.session.execute(count_stmt)
            total = count_result.scalar() or 0
            
            return AppointmentListResponse(
                items=[AppointmentResponse.model_validate(r) for r in appointments],
                total=total
            )
        except Exception as e:
            logger.error(f"Error listing appointments: {e}", exc_info=True)
            raise e

    @post("/", guards=[PermissionGuard(PermissionEnum.SCHEDULE_MANAGE)])
    async def create_appointment(
        self, 
        data: AppointmentCreate, 
        appointment_repo: AppointmentRepository
    ) -> AppointmentResponse:
        """Tạo mới một phiên làm việc "Elite" trong hệ thống."""
        import uuid
        appointment = Appointment(
            id=str(uuid.uuid4()),
            **data.model_dump()
        )
        created = await appointment_repo.add(appointment)
        await appointment_repo.session.commit()
        return AppointmentResponse.model_validate(created)

    @get("/{appointment_id:uuid}")
    async def get_appointment(
        self, 
        appointment_id: UUID, 
        appointment_repo: AppointmentRepository
    ) -> AppointmentResponse:
        """Truy xuất chi tiết một phiên làm việc cụ thể."""
        appointment = await appointment_repo.get(str(appointment_id))
        from litestar.exceptions import NotFoundException
        if not appointment:
            raise NotFoundException(f"Không tìm thấy lịch hẹn {appointment_id}")
        return AppointmentResponse.model_validate(appointment)

    @patch("/{appointment_id:uuid}", guards=[PermissionGuard(PermissionEnum.SCHEDULE_MANAGE)])
    async def update_appointment(
        self, 
        appointment_id: UUID, 
        data: AppointmentUpdate, 
        appointment_repo: AppointmentRepository
    ) -> AppointmentResponse:
        """Cập nhật thông tin phiên làm việc theo yêu cầu của Sếp."""
        appointment = await appointment_repo.get(str(appointment_id))
        if not appointment:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"Không tìm thấy lịch hẹn {appointment_id}")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(appointment, key, value)
            
        updated = await appointment_repo.update(appointment)
        await appointment_repo.session.commit()
        return AppointmentResponse.model_validate(updated)

    @delete("/{appointment_id:uuid}", guards=[PermissionGuard(PermissionEnum.SCHEDULE_MANAGE)])
    async def delete_appointment(
        self, 
        appointment_id: UUID, 
        appointment_repo: AppointmentRepository
    ) -> None:
        """Xóa bỏ một phiên làm việc khỏi hệ thống."""
        await appointment_repo.delete(str(appointment_id))
        await appointment_repo.session.commit()
