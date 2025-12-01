class BasicCRMBackend:
    """Fallback cuando Prometeo está caído"""
    
    def create_lead(self, contact_data):
        # Guardar lead básico en Janis
        lead = Lead.objects.create(**contact_data)
        return lead
    
    def calculate_score(self, lead_data):
        # Scoring básico
        score = 0
        if lead_data.get('property_value', 0) > 100000:
            score += 30
        if lead_data.get('urgency') == 'high':
            score += 40
        return min(score, 100)