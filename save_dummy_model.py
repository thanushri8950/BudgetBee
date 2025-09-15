# save_dummy_model.py
import joblib

class DummyPipeline:
    def predict(self, X):
        # Always predicts "Other"
        return ["Other" for _ in X]

joblib.dump(DummyPipeline(), "budgetbee_pipeline.joblib")
print("✅ Dummy pipeline saved as budgetbee_pipeline.joblib")
