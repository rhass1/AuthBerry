#! /usr/bin/env python3

from backend.extensions import db
from datetime import datetime


class SystemSetting(db.Model):
    """Model for system-wide settings and configurations"""
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=True)
    value_type = db.Column(db.String(20), nullable=False, default='string')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get_setting(key, default=None):
        """Get a system setting by key with type conversion"""
        setting = SystemSetting.query.filter_by(key=key).first()
        
        if not setting:
            return default
            
        # Convert value based on type
        if setting.value_type == 'boolean':
            return setting.value.lower() == 'true'
        elif setting.value_type == 'int':
            return int(setting.value)
        elif setting.value_type == 'float':
            return float(setting.value)
        
        # Default string value
        return setting.value
    
    @staticmethod
    def set_setting(key, value, value_type='string'):
        """Set a system setting, creating it if it doesn't exist"""
        # Convert value to string for storage
        str_value = str(value).lower() if value_type == 'boolean' else str(value)
        
        setting = SystemSetting.query.filter_by(key=key).first()
        if setting:
            setting.value = str_value
            setting.value_type = value_type
            setting.updated_at = datetime.utcnow()
        else:
            setting = SystemSetting(
                key=key, 
                value=str_value,
                value_type=value_type
            )
            db.session.add(setting)
            
        db.session.commit()
        return setting
    
    # Default settings initialization
    @staticmethod
    def initialize_defaults():
        """Initialize default system settings if they don't exist"""
        defaults = {
            'registration_enabled': ('true', 'boolean'),
            'system_name': ('AuthBerry_Backup', 'string'),
            'max_login_attempts': ('5', 'int'),
        }
        
        for key, (value, value_type) in defaults.items():
            # Only set if setting doesn't exist
            if not SystemSetting.query.filter_by(key=key).first():
                SystemSetting.set_setting(key, value, value_type) 
