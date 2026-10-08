import os

# Never load backend/.env while running tests.
os.environ["ENVIRONMENT"] = "test"
os.environ["JWT_SECRET_KEY"] = "unit-tests-only-secret-with-at-least-32-characters"
os.environ["TICKET_SECRET_KEY"] = "different-unit-tests-only-secret-at-least-32-characters"
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://test:test@localhost/college_events_test"
)
os.environ["UPLOAD_DIR"] = ".test-uploads"
