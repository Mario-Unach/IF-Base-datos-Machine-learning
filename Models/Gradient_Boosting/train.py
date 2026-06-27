import xgboost as xgb
from sklearn.model_selection import GridSearchCV
import joblib
import os

def train_and_save_xgboost(X_train, y_train, scale_pos_weight, medians, columns, save_dir):
    """Entrena XGBoost con GridSearch y guarda todos los artefactos"""
    param_grid = {'n_estimators': [100, 150], 'max_depth': [4, 6], 'learning_rate': [0.05, 0.1]}
    
    model = xgb.XGBClassifier(scale_pos_weight=scale_pos_weight, random_state=42, 
                              use_label_encoder=False, eval_metric='logloss', verbosity=0)
    
    grid = GridSearchCV(model, param_grid, scoring='roc_auc', cv=3, n_jobs=-1, verbose=1)
    grid.fit(X_train, y_train)
    best_model = grid.best_estimator_
    
    os.makedirs(save_dir, exist_ok=True)
    joblib.dump(best_model, os.path.join(save_dir, 'xgb_model.pkl'))
    joblib.dump(medians, os.path.join(save_dir, 'medians.pkl'))
    joblib.dump(list(columns), os.path.join(save_dir, 'columns.pkl'))
    
    print(f"✅ Modelo y artefactos guardados en {save_dir}")
    return best_model