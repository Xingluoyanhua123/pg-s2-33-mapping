import json
import os
import time

os.environ['AI_LLM_PROVIDER'] = os.environ.get('TEST_LLM_PROVIDER', 'mock')
os.environ['AI_EMBEDDING_PROVIDER'] = os.environ.get('TEST_EMBEDDING_PROVIDER', 'mock')

from app.services.mapping_service import CreditMappingOrchestrator
from app.services.llm_provider import get_llm_provider
from app.services.embedding_provider import get_embedding_provider
from app.services.vector_store import InMemoryVectorStore
from app.services.retrieval_service import SemanticRetrievalService
from app.config import settings

print(f"Running test with LLM provider={settings.llm_provider}, embedding provider={settings.embedding_provider}")

llm_provider = get_llm_provider(settings.llm_provider, settings.llm_model_name)
embedding_provider = get_embedding_provider(settings.embedding_provider, settings.embedding_model_name)
vector_store = InMemoryVectorStore()
retrieval_service = SemanticRetrievalService(embedding_provider, vector_store)

print("Indexing real course catalog from PostgreSQL...")
start = time.time()
orchestrator = CreditMappingOrchestrator(retrieval_service=retrieval_service, llm_provider=llm_provider)
print(f"Indexing complete in {time.time()-start:.1f}s")

with open('synthetic_students.json') as f:
    students = json.load(f)

correct = 0
results = []
start = time.time()

for i, student in enumerate(students):
    result = orchestrator.run(student)
    predicted_code = result.get('top_match', {}).get('course_code')
    expected_code = student['expected_course_code']
    is_correct = predicted_code == expected_code
    if is_correct:
        correct += 1

    results.append({
        'student_id': student['student_id'],
        'expected': expected_code,
        'predicted': predicted_code,
        'correct': is_correct,
        'similarity_score': result.get('top_match', {}).get('similarity_score')
    })

    if (i + 1) % 10 == 0:
        print(f"[{i+1}/100] Running accuracy so far: {correct}/{i+1} ({100*correct/(i+1):.1f}%)")

total_time = time.time() - start
accuracy = correct / len(students) * 100

print(f"\n=== FINAL RESULTS ===")
print(f"Correct: {correct}/{len(students)} ({accuracy:.1f}%)")
print(f"Total time: {total_time:.1f}s ({total_time/len(students):.2f}s per student)")

with open('test_100_students_results.json', 'w') as f:
    json.dump({
        'llm_provider': settings.llm_provider,
        'embedding_provider': settings.embedding_provider,
        'accuracy_percent': accuracy,
        'correct': correct,
        'total': len(students),
        'avg_time_per_student_sec': total_time / len(students),
        'details': results
    }, f, indent=2)

print("Full results saved to test_100_students_results.json")
