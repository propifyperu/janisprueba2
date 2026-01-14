import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'janis_core3.settings')
django.setup()

from properties.models import Lead, WhatsAppConversation
from django.db.models import OuterRef, Subquery

def test_query():
    print("Testing Lead annotation query...")
    try:
        leads = Lead.objects.all()
        last_msg_qs = WhatsAppConversation.objects.filter(lead=OuterRef('pk')).order_by('-created_at')
        
        # Determine annotation names
        # ORIGINAL ERROR was: .annotate(last_message_at=...) colliding with model field
        
        print("Attempting annotation with 'annotated_last_message_at'...")
        leads = leads.annotate(
            annotated_last_message=Subquery(last_msg_qs.values('message_body')[:1]),
            annotated_last_message_at=Subquery(last_msg_qs.values('created_at')[:1])
        )
        
        # Force evaluation
        count = leads.count()
        print(f"Query successful. Count: {count}")
        
        if count > 0:
            l = leads.first()
            print(f"First lead: {l}")
            print(f"Has 'annotated_last_message_at': {hasattr(l, 'annotated_last_message_at')}")
            print(f"Value: {l.annotated_last_message_at}")
            
    except Exception as e:
        print(f"QUERY FAILED: {e}")
        import traceback
        traceback.print_exc()

def check_db_content():
    print("\nChecking DB content...")
    print(f"Leads count: {Lead.objects.count()}")
    print(f"Conversations count: {WhatsAppConversation.objects.count()}")
    
    last_conv = WhatsAppConversation.objects.order_by('-created_at').first()
    if last_conv:
        print(f"Last conversation: {last_conv.created_at} - {last_conv.message_body}")
    else:
        print("No conversations found.")

if __name__ == '__main__':
    test_query()
    check_db_content()
