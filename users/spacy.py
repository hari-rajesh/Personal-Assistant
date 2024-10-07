import spacy
import dateparser
from datetime import datetime
from .models import Task
from django.utils import timezone


nlp = spacy.load("en_core_web_sm")

def identify_intent_and_entities(user_input):
    doc = nlp(user_input.lower())
    print(doc)
    intent = None
    date = None

    if "agenda" in user_input:
        intent = "agenda"
    elif "pending tasks" in user_input:
        intent = "pending_tasks"
    elif "reschedule" in user_input:
        intent = "reschedule"

    # Parse for date
    for ent in doc.ents:
        if ent.label_ in ['DATE', 'TIME']:
            date = dateparser.parse(ent.text, settings={'RELATIVE_BASE': datetime.now()})
    
    return intent, date



def handle_user_query(user, user_input):
    intent, query_date = identify_intent_and_entities(user_input)
    
    if intent == "agenda":
        if not query_date:
            query_date = timezone.now().date()
        tasks = Task.objects.filter(user=user, deadline__date=query_date, status='Pending')
        return tasks

    elif intent == "pending_tasks":
        tasks = Task.objects.filter(user=user, status='Pending')
        return tasks

    elif intent == "reschedule":
        # Implement rescheduling logic
        return "Reschedule functionality coming soon."
    
    return "Sorry, I couldn't understand your request."


def suggest_tasks(user):
    from .models import Task
    now = timezone.now()

    recommended_tasks = Task.objects.filter(
        user=user,
        deadline__gt=now,
        status__in=['Pending', 'In Progress']
    ).order_by('deadline', '-priority')

    return recommended_tasks[:5]