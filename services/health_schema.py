"""Shared health field definitions; measurements are never outcome labels."""
HEALTH_REQUIRED = ('resting_hr', 'hrv', 'sleep_hours', 'sleep_quality', 'soreness', 'fatigue', 'stress', 'energy_level', 'hydration_status')
HEALTH_OPTIONAL = ('weight', 'body_fat_pct', 'blood_pressure_sys', 'blood_pressure_dia', 'oxygen_saturation', 'body_temperature')
MEDICAL_FIELDS = ('hemoglobin', 'hematocrit', 'wbc_count', 'platelet_count', 'ferritin', 'serum_iron', 'vitamin_d', 'vitamin_b12', 'glucose', 'creatinine', 'crp')
