from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.database.dependencies import get_db
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.user import User
from app.schemas.organization import OrganizationCreate

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post("", status_code=201)
def create_organization(
    organization_data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    organization = Organization(name=organization_data.name.strip())
    db.add(organization)
    db.flush()
    membership = OrganizationMember(
        user_id=current_user.id,
        organization_id=organization.id,
        role="owner",
    )
    db.add(membership)
    db.commit()
    db.refresh(organization)
    return {
        "id": str(organization.id),
        "name": organization.name,
        "role": membership.role,
    }


@router.get("")
def list_my_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    memberships = (
        db.query(OrganizationMember, Organization)
        .join(Organization, Organization.id == OrganizationMember.organization_id)
        .filter(OrganizationMember.user_id == current_user.id)
        .all()
    )
    return [
        {"id": str(org.id), "name": org.name, "role": member.role}
        for member, org in memberships
    ]