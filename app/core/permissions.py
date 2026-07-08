from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.permissions import Permission, RolePermission, UserPermission
from app.models.user import User


class PermissionService:
    """Құқықтар басқару қызметі"""
    
    @staticmethod
    def has_permission(user: User, permission_name: str, db: Session) -> bool:
        """
        Пайдаланушының құқығын тексеру
        """
        # Superadmin барлық құқыққа ие
        if user.role.value == "superadmin":
            return True
        
        # Рөлдік құқықтарды тексеру
        role_permission = db.query(RolePermission).join(Permission).filter(
            RolePermission.role == user.role.value,
            Permission.name == permission_name,
            RolePermission.is_granted == True
        ).first()
        
        if role_permission:
            return True
        
        # Жеке құқықтарды тексеру
        user_permission = db.query(UserPermission).join(Permission).filter(
            UserPermission.user_id == user.id,
            Permission.name == permission_name,
            UserPermission.is_granted == True
        ).first()
        
        if user_permission:
            return True
        
        return False
    
    @staticmethod
    def get_user_permissions(user: User, db: Session) -> List[str]:
        """
        Пайдаланушының барлық құқықтары
        """
        if user.role.value == "superadmin":
            # Superadmin үшін барлық құқықтар
            permissions = db.query(Permission).all()
            return [p.name for p in permissions]
        
        # Рөлдік құқықтар
        role_permissions = db.query(Permission.name).join(RolePermission).filter(
            RolePermission.role == user.role.value,
            RolePermission.is_granted == True
        ).all()
        
        role_permission_names = [p[0] for p in role_permissions]
        
        # Жеке құқықтар
        user_permissions = db.query(Permission.name).join(UserPermission).filter(
            UserPermission.user_id == user.id,
            UserPermission.is_granted == True
        ).all()
        
        user_permission_names = [p[0] for p in user_permissions]
        
        # Біріктіру
        all_permissions = list(set(role_permission_names + user_permission_names))
        
        return all_permissions
    
    @staticmethod
    def grant_role_permission(role: str, permission_name: str, db: Session) -> bool:
        """
        Рөлге құқық беру
        """
        permission = db.query(Permission).filter(Permission.name == permission_name).first()
        if not permission:
            return False
        
        existing = db.query(RolePermission).filter(
            RolePermission.role == role,
            RolePermission.permission_id == permission.id
        ).first()
        
        if existing:
            existing.is_granted = True
        else:
            new_role_permission = RolePermission(
                role=role,
                permission_id=permission.id,
                is_granted=True
            )
            db.add(new_role_permission)
        
        db.commit()
        return True
    
    @staticmethod
    def revoke_role_permission(role: str, permission_name: str, db: Session) -> bool:
        """
        Рөлден құқық алу
        """
        permission = db.query(Permission).filter(Permission.name == permission_name).first()
        if not permission:
            return False
        
        role_permission = db.query(RolePermission).filter(
            RolePermission.role == role,
            RolePermission.permission_id == permission.id
        ).first()
        
        if role_permission:
            role_permission.is_granted = False
            db.commit()
            return True
        
        return False
    
    @staticmethod
    def grant_user_permission(user_id: int, permission_name: str, db: Session) -> bool:
        """
        Пайдаланушыға құқық беру
        """
        permission = db.query(Permission).filter(Permission.name == permission_name).first()
        if not permission:
            return False
        
        existing = db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.permission_id == permission.id
        ).first()
        
        if existing:
            existing.is_granted = True
        else:
            new_user_permission = UserPermission(
                user_id=user_id,
                permission_id=permission.id,
                is_granted=True
            )
            db.add(new_user_permission)
        
        db.commit()
        return True
    
    @staticmethod
    def revoke_user_permission(user_id: int, permission_name: str, db: Session) -> bool:
        """
        Пайдаланушыдан құқық алу
        """
        permission = db.query(Permission).filter(Permission.name == permission_name).first()
        if not permission:
            return False
        
        user_permission = db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.permission_id == permission.id
        ).first()
        
        if user_permission:
            user_permission.is_granted = False
            db.commit()
            return True
        
        return False
    
    @staticmethod
    def initialize_default_permissions(db: Session):
        """
        Әдепкі құқықтарды инициализациялау
        """
        # Тендер модулі
        tender_permissions = [
            ("tender.create", "Тендер жасау", "tenders", "create", "tender"),
            ("tender.read", "Тендерлерді көру", "tenders", "read", "tender"),
            ("tender.update", "Тендерді жаңарту", "tenders", "update", "tender"),
            ("tender.delete", "Тендерді жою", "tenders", "delete", "tender"),
            ("tender.approve", "Тендерді бекіту", "tenders", "approve", "tender"),
        ]
        
        # Пайдаланушылар модулі
        user_permissions = [
            ("user.create", "Пайдаланушы жасау", "users", "create", "user"),
            ("user.read", "Пайдаланушыларды көру", "users", "read", "user"),
            ("user.update", "Пайдаланушыларды жаңарту", "users", "update", "user"),
            ("user.delete", "Пайдаланушыларды жою", "users", "delete", "user"),
            ("user.manage_roles", "Рөлдерді басқару", "users", "manage", "role"),
        ]
        
        # Есептер модулі
        report_permissions = [
            ("report.create", "Есеп жасау", "reports", "create", "report"),
            ("report.read", "Есептерді көру", "reports", "read", "report"),
            ("report.export", "Есептерді экспорттау", "reports", "export", "report"),
        ]
        
        # Аналитика модулі
        analytics_permissions = [
            ("analytics.view", "Аналитика көру", "analytics", "view", "dashboard"),
            ("analytics.export", "Аналитика экспорттау", "analytics", "export", "dashboard"),
        ]
        
        # Бөлімдер модулі
        department_permissions = [
            ("department.create", "Бөлім жасау", "departments", "create", "department"),
            ("department.read", "Бөлімдерді көру", "departments", "read", "department"),
            ("department.update", "Бөлімдерді жаңарту", "departments", "update", "department"),
            ("department.delete", "Бөлімдерді жою", "departments", "delete", "department"),
        ]
        
        # Барлық құқықтарды біріктіру
        all_permissions = (
            tender_permissions + user_permissions + report_permissions + 
            analytics_permissions + department_permissions
        )
        
        for perm_name, description, module, action, resource in all_permissions:
            existing = db.query(Permission).filter(Permission.name == perm_name).first()
            if not existing:
                new_permission = Permission(
                    name=perm_name,
                    description=description,
                    module=module,
                    action=action,
                    resource=resource
                )
                db.add(new_permission)
        
        db.commit()
        
        # Әдепкі рөлдік құқықтар
        default_role_permissions = {
            "superadmin": [p[0] for p in all_permissions],  # Барлық құқықтар
            "buyer": [
                "tender.create", "tender.read", "tender.update", "tender.approve",
                "report.read", "report.export",
                "analytics.view", "analytics.export",
            ],
            "procurement_manager": [
                "tender.create", "tender.read", "tender.update", "tender.approve",
                "report.read", "report.export",
                "analytics.view", "analytics.export",
            ],
            "department_head": [
                "tender.read", "tender.approve",
                "report.read",
                "analytics.view",
            ],
            "employee": [
                "tender.read",
                "report.read",
            ],
            "supplier": [
                "tender.read",
                "report.read",
            ],
        }
        
        for role, permission_names in default_role_permissions.items():
            for perm_name in permission_names:
                permission = db.query(Permission).filter(Permission.name == perm_name).first()
                if permission:
                    existing = db.query(RolePermission).filter(
                        RolePermission.role == role,
                        RolePermission.permission_id == permission.id
                    ).first()
                    
                    if not existing:
                        new_role_permission = RolePermission(
                            role=role,
                            permission_id=permission.id,
                            is_granted=True
                        )
                        db.add(new_role_permission)
        
        db.commit()
