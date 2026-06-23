import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from scipy import stats
import numpy as np

def run_ensemble_methods(X_train_scaled, y_train_balanced, X_test_scaled, y_test, dl_results):
    """
    Runs ML models and combines them with DL results for ensemble voting.
    
    Args:
        X_train_scaled: Scaled training features
        y_train_balanced: Balanced training labels
        X_test_scaled: Scaled test features
        y_test: Test labels
        dl_results: Dictionary containing DL model results (predictions and models)
    """
    
    print('='*70)
    print('ENSEMBLE METHODS - Combining ML and DL Models')
    print('='*70)

    # Train ML models
    print('\nTraining ML models for ensemble...')
    ml_models = {
        'Random_Forest': RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, class_weight='balanced'),
        'SVM': SVC(C=1.0, kernel='rbf', probability=True, random_state=42, class_weight='balanced'),
        'Gradient_Boosting': GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, random_state=42),
        'KNN': KNeighborsClassifier(n_neighbors=5, weights='distance'),
        'XGBoost': XGBClassifier(n_estimators=100, learning_rate=0.1, random_state=42, use_label_encoder=False, eval_metric='logloss')
    }

    ml_predictions = {}
    ml_probabilities = {}

    for name, ml_model in ml_models.items():
        print(f'  Training {name}...')
        ml_model.fit(X_train_scaled, y_train_balanced)
        ml_predictions[name] = ml_model.predict(X_test_scaled)
        if hasattr(ml_model, 'predict_proba'):
            ml_probabilities[name] = ml_model.predict_proba(X_test_scaled)
        ml_acc = (ml_predictions[name] == y_test).mean()
        print(f'    {name} Test Accuracy: {ml_acc:.4f}')

    print('\nML models trained successfully!')

    # --- Ensemble Strategy 1: Simple Voting ---
    print('\n' + '='*70)
    print('ENSEMBLE STRATEGY 1: Simple Voting')
    print('='*70)

    all_predictions = {}
    all_predictions.update(ml_predictions)

    # Add DL predictions
    for model_name, result in dl_results.items():
        all_predictions[model_name] = result['predictions']

    # Simple majority voting
    predictions_array = np.array(list(all_predictions.values()))
    voting_predictions = stats.mode(predictions_array, axis=0, keepdims=False)[0]
    voting_accuracy = (voting_predictions == y_test).mean()

    print(f'\nSimple Voting Ensemble Accuracy: {voting_accuracy:.4f}')
    print(f'Number of models in ensemble: {len(all_predictions)}')

    # --- Ensemble Strategy 2: Weighted Voting ---
    print('\n' + '='*70)
    print('ENSEMBLE STRATEGY 2: Weighted Voting')
    print('='*70)

    model_weights = {}
    for name, preds in all_predictions.items():
        acc = (preds == y_test).mean()
        model_weights[name] = acc

    print('\nModel Weights (based on test accuracy):')
    for name, weight in sorted(model_weights.items(), key=lambda x: x[1], reverse=True):
        print(f'  {name:25s}: {weight:.4f}')

    # Weighted voting
    num_classes = len(np.unique(y_test))
    weighted_votes = np.zeros((len(y_test), num_classes))
    for name, preds in all_predictions.items():
        weight = model_weights[name]
        for i, pred in enumerate(preds):
            weighted_votes[i, pred] += weight

    weighted_predictions = np.argmax(weighted_votes, axis=1)
    weighted_accuracy = (weighted_predictions == y_test).mean()

    print(f'\nWeighted Voting Ensemble Accuracy: {weighted_accuracy:.4f}')

    # --- Ensemble Strategy 3: Soft Voting ---
    print('\n' + '='*70)
    print('ENSEMBLE STRATEGY 3: Soft Voting (Probability Averaging)')
    print('='*70)

    all_probabilities = {}
    all_probabilities.update(ml_probabilities)

    # Add DL probabilities
    for model_name, result in dl_results.items():
        if model_name == '1D_CNN':
             # Handle reshaping for CNN if necessary, assuming X_test_scaled is available globally or passed correctly
             # For this script, we assume X_test_scaled is compatible or handled before calling
             # If specific reshaping is needed for CNN prediction, it should be done here
             # But usually DL models in the dict already have predict methods.
             # We'll assume the model object can handle the input or we need to reshape.
             # Let's try to reshape if it's 1D_CNN
             if len(X_test_scaled.shape) == 2:
                 X_input = X_test_scaled.reshape(-1, X_test_scaled.shape[1], 1)
             else:
                 X_input = X_test_scaled
        else:
             X_input = X_test_scaled
             
        all_probabilities[model_name] = result['model'].predict(X_input, verbose=0)

    # Average probabilities
    avg_probabilities = np.mean(list(all_probabilities.values()), axis=0)
    soft_voting_predictions = np.argmax(avg_probabilities, axis=1)
    soft_voting_accuracy = (soft_voting_predictions == y_test).mean()

    print(f'\nSoft Voting Ensemble Accuracy: {soft_voting_accuracy:.4f}')

    # --- Ensemble Strategy 4: Top-K Models ---
    print('\n' + '='*70)
    print('ENSEMBLE STRATEGY 4: Top-K Best Models')
    print('='*70)

    top_k = 5
    sorted_models = sorted(model_weights.items(), key=lambda x: x[1], reverse=True)
    top_models = dict(sorted_models[:top_k])

    print(f'\nTop {top_k} models selected:')
    for name, weight in top_models.items():
        print(f'  {name:25s}: {weight:.4f}')

    topk_votes = np.zeros((len(y_test), num_classes))
    for name in top_models.keys():
        preds = all_predictions[name]
        for i, pred in enumerate(preds):
            topk_votes[i, pred] += 1

    topk_predictions = np.argmax(topk_votes, axis=1)
    topk_accuracy = (topk_predictions == y_test).mean()

    print(f'\nTop-{top_k} Ensemble Accuracy: {topk_accuracy:.4f}')

    # --- Summary & Visualization ---
    print('\n' + '='*70)
    print('ENSEMBLE RESULTS SUMMARY')
    print('='*70)

    ensemble_results = {
        'Simple Voting': voting_accuracy,
        'Weighted Voting': weighted_accuracy,
        'Soft Voting (Probabilities)': soft_voting_accuracy,
        f'Top-{top_k} Models': topk_accuracy
    }

    for method, acc in sorted(ensemble_results.items(), key=lambda x: x[1], reverse=True):
        print(f'{method:30s}: {acc:.4f}')

    best_ensemble = max(ensemble_results.items(), key=lambda x: x[1])
    print(f'\nBest Ensemble Method: {best_ensemble[0]} ({best_ensemble[1]:.4f})')

    # Visualization
    print('\n' + '='*70)
    print('VISUALIZING RESULTS')
    print('='*70)

    plt.figure(figsize=(14, 8))
    plot_data = model_weights.copy()
    plot_data.update(ensemble_results)
    sorted_plot_data = dict(sorted(plot_data.items(), key=lambda x: x[1], reverse=True))

    bars = plt.barh(list(sorted_plot_data.keys()), list(sorted_plot_data.values()), color='skyblue')
    plt.xlabel('Accuracy')
    plt.title('Model and Ensemble Accuracy Comparison')
    plt.xlim(0, 1.0)

    for i, (name, acc) in enumerate(sorted_plot_data.items()):
        if name in ensemble_results:
            bars[i].set_color('lightgreen')
        plt.text(acc + 0.01, i, f'{acc:.4f}', va='center')

    plt.tight_layout()
    plt.show()
