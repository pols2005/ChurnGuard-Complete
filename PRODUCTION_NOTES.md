# ChurnGuard Production Notes

This document tracks features, models, and configurations that have been temporarily disabled or modified for testing/development purposes and need to be restored for production deployment.

## 🚨 **Items Requiring Production Restoration**

### Machine Learning Models

#### **GBoosting Model - DISABLED** ⚠️
- **File**: `churn-prediction/server/app.py`
- **Line**: ~39 in `model_files` dict
- **Status**: Commented out due to scikit-learn version incompatibility
- **Issue**: `AttributeError: Can't get attribute '__pyx_unpickle_CyHalfBinomialLoss'`
- **Cause**: Model trained with older scikit-learn version (1.5.2), AWS server has 1.7.1
- **Production Fix Required**: 
  ```python
  # Current (disabled):
  # 'GBoosting': 'gb_model.pkl',  # Commented out due to scikit-learn version compatibility
  
  # Production restore:
  'GBoosting': 'gb_model.pkl',
  ```

#### **Other Disabled Models** 
- **DecisionTree**: `dt_model.pkl` - Currently commented out
- **RandomForest**: `rf_model.pkl` - Currently commented out  
- **GaussianNB**: `nb_model.pkl` - Currently commented out
- **SVC**: `svm_model.pkl` - Currently commented out
- **LogisticReg**: `lr_model.pkl` - Currently commented out

**Production Action Required**: 
1. **Re-train all models** with current scikit-learn versions in production environment
2. **OR** Use model serialization format compatible across versions (`.joblib` instead of `.pickle`)
3. **OR** Pin scikit-learn versions to match training environment

### CORS Configuration

#### **CORS Origins - MODIFIED** ⚠️
- **File**: `churn-prediction/server/app.py`
- **Line**: ~16
- **Current**: `CORS(app)` - Allows all origins for development
- **Production Required**: 
  ```python
  # Development (current):
  CORS(app)
  
  # Production (restore):
  CORS(app, supports_credentials=True, origins=["https://your-production-domain.com"])
  ```

### Authentication & Security

#### **Mock Authentication - DEVELOPMENT ONLY** ⚠️
- **File**: `churn-prediction/server/app.py`
- **Endpoint**: `/api/auth/me` (line ~469)
- **Status**: Returns hardcoded mock user data
- **Production Action**: Replace with real authentication system
- **Current Issue**: No real user verification, permissions, or session management

### Data Sources

#### **Static CSV Data** ⚠️
- **File**: All endpoints reading `churn.csv`
- **Status**: Using static demo dataset
- **Production Required**: Connect to real customer database
- **Files to update**: All endpoints using `pd.read_csv('churn.csv')`

---

## 🔧 **Production Deployment Checklist**

### Before Production:

- [ ] **Retrain ML Models** with production scikit-learn version
- [ ] **Update CORS configuration** to restrict origins
- [ ] **Implement real authentication** system
- [ ] **Connect to production database** instead of CSV files
- [ ] **Set environment variables** properly
- [ ] **Configure SSL/HTTPS** 
- [ ] **Enable logging** and monitoring
- [ ] **Set up proper error handling** for production
- [ ] **Configure rate limiting** on API endpoints
- [ ] **Test all v2 API endpoints** with real data

### Model Compatibility Solutions:

1. **Option 1 - Retrain Models:**
   ```bash
   pip install scikit-learn==1.7.1 xgboost==latest
   # Retrain all models with new versions
   # Save with joblib instead of pickle for better compatibility
   ```

2. **Option 2 - Version Pinning:**
   ```bash
   pip install scikit-learn==1.5.2
   # Match the training environment versions
   ```

3. **Option 3 - Model Export/Import:**
   ```python
   # For XGBoost models, use native save/load instead of pickle
   model.save_model('xgb_model.json')
   model.load_model('xgb_model.json')
   ```

### Security Hardening:

```python
# Production app.py changes needed:

# 1. Proper CORS
CORS(app, supports_credentials=True, origins=["https://yourdomain.com"])

# 2. Add rate limiting
from flask_limiter import Limiter
limiter = Limiter(app, key_func=get_remote_address)
@limiter.limit("10 per minute")

# 3. Add input validation
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

# 4. Environment-based configuration
if os.environ.get('FLASK_ENV') != 'development':
    app.config['DEBUG'] = False
```

---

## 📋 **Testing Status**

### ✅ **Working in Development:**
- v2 Dashboard API endpoints
- XGBoost, KNeighbors, ExtraTrees, AdaBoost models
- Basic churn prediction functionality
- Mock authentication for dashboard
- CORS configuration for cross-origin requests

### ⚠️ **Needs Production Testing:**
- GBoosting model loading
- Real authentication integration
- Database connections
- SSL/HTTPS configuration
- Performance under load

---

## 📝 **Version History**

- **2025-09-02**: Initial production notes created
  - GBoosting model disabled due to scikit-learn compatibility
  - CORS opened for development
  - Mock authentication implemented
  - All v2 API endpoints added and tested

---

**⚠️ IMPORTANT**: This file should be reviewed and updated before each production deployment to ensure all disabled features are properly restored and tested.