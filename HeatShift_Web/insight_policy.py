"""Fail-closed scope checks around Mateen's preserved retrieval agent.

Support a small, explicit grammar. Unknown wording, mixed requests, forecasts,
location/date filters and personal recommendations never fall through to a
generic historical summary. This deliberately favors abstention over coverage.
"""
import re

GUIDANCE = {
    'scope': ('Temperature prediction scope', [
        'what does heatshift predict', 'explain the prediction scope',
        'what is the forecast horizon', 'which stations are supported',
        'what are the supported cities',
    ]),
    'uncertainty': ('Uncertainty and baseline', [
        'explain uncertainty', 'explain the uncertainty range',
        'what does the uncertainty range mean', 'what does the error range mean',
        'what is the baseline', 'explain the baseline',
    ]),
    'quality': ('Data quality and interpolation', [
        'explain data quality', 'explain interpolation',
        'how should i use cleaned data', 'what does the quality agent do',
    ]),
    'citations': ('Historical evidence and citations', [
        'explain citations', 'what do the row ids mean',
        'where do the insight numbers come from', 'explain the evidence limits',
    ]),
}

def classify(question, city):
    if not isinstance(question, str) or not question.strip() or len(question)>500:
        return {'intent':'refuse','reason':'The question is empty or too long.'}
    q=re.sub(r'\s+',' ',question.lower().replace('’',"'")).strip().rstrip('?.!').strip()
    # Full matches are essential: appending another request must cause refusal.
    for key,(section,phrases) in GUIDANCE.items():
        if q in phrases:return {'intent':'guidance','topic':key,'section':section}
    name=re.escape(city.lower())
    city_part=rf'(?: (?:in|for|at) {name})?'
    historical=rf'(?:the )?(?:(?:recorded|historical|training) )?(?:temperature|temperatures|weather|weather data|data)'
    if q == 'what are the minimum and maximum recorded temperatures':
        return {'intent':'statistics'}
    patterns=[
        rf'(?:summarize|summarise|describe|show|give me)(?: the)? (?:recorded|historical|training) (?:temperature|temperatures|weather|weather data|data){city_part}',
        rf'(?:summarize|summarise) (?:temperature|temperatures|weather|weather data){city_part}',
        rf'(?:temperature summary|recorded extremes|recorded temperature extremes){city_part}',
        rf'(?:what (?:is|was|are|were)|show|give me) (?:the )?(?:average|mean|minimum|maximum|lowest|highest) (?:recorded |historical |training )?temperature{city_part}',
        rf'(?:what (?:is|was|are|were)|show) (?:the )?(?:recorded |historical )?temperature (?:minimum and maximum|extremes){city_part}',
    ]
    if any(re.fullmatch(p,q) for p in patterns):return {'intent':'statistics'}
    return {'intent':'refuse','reason':
        'The available gold table only supports whole-table historical temperature summaries '
        f'for the selected station ({city}). This question requests an unsupported location, '
        'time, quantity, recommendation, or wording. No current or future answer is inferred '
        'from historical averages. Try "Summarize recorded temperature" or one of the guidance prompts.'}
