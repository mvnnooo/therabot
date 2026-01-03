class MySQLMemoryManager:
    def __init__(self, config: Dict[str, Any] = None):
        if config is None:
            # إعدادات افتراضية للاتصال بـ PythonAnywhere
            config = {
                'host': os.getenv('DB_HOST', 'mvnnooo.mysql.pythonanywhere-services.com'),
                'user': os.getenv('DB_USER', 'mvnnooo'),
                'password': os.getenv('DB_PASSWORD', ''),
                'database': os.getenv('DB_NAME', 'mvnnooo$therabot_db'),
                'port': int(os.getenv('DB_PORT', 3306)),
                'use_pure': True,  # مهم لـ PythonAnywhere
                'ssl_disabled': True,  # إذا لم يكن SSL مفعلاً
            }
        
        # إضافة إعدادات SSL إذا مطلوب
        if not config.get('ssl_disabled', False):
            config['ssl_ca'] = '/path/to/ca.pem'
            config['ssl_cert'] = '/path/to/client-cert.pem'
            config['ssl_key'] = '/path/to/client-key.pem'
        
        try:
            # اختبار الاتصال مباشرة
            test_connection = mysql.connector.connect(**config)
            test_connection.close()
            print("✅ Connected to PythonAnywhere MySQL successfully!")
            
            # إنشاء connection pool
            config['pool_name'] = 'pythonanywhere_pool'
            config['pool_size'] = 3  # PythonAnywhere يسمح بعدد محدود من الاتصالات
            self.connection_pool = pooling.MySQLConnectionPool(**config)
            
        except mysql.connector.Error as err:
            print(f"❌ Failed to connect to PythonAnywhere MySQL: {err}")
            print("Trying local fallback...")
            self._setup_local_fallback()
    
    def _setup_local_fallback(self):
        """إنشاء اتصال محلي كبديل إذا فشل الاتصال البعيد"""
        local_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'therabot_db_local',
            'pool_name': 'local_fallback_pool',
            'pool_size': 2
        }
        try:
            self.connection_pool = pooling.MySQLConnectionPool(**local_config)
            print("✅ Using local MySQL as fallback")
        except:
            print("⚠️ Using in-memory storage only")
            self.connection_pool = None
