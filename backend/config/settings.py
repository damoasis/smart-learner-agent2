"""
应用配置管理模块
使用Pydantic Settings从环境变量加载配置
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    app_name: str = Field(default="Smart Learner Agent", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    secret_key: str = Field(..., alias="SECRET_KEY")
    
    # 数据库配置
    database_url: str = Field(..., alias="DATABASE_URL")
    db_echo: bool = Field(default=False, alias="DB_ECHO")
    
    # Redis配置
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_max_connections: int = Field(default=50, alias="REDIS_MAX_CONNECTIONS")
    
    # OpenAI配置
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", alias="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.7, alias="OPENAI_TEMPERATURE")
    embedding_model: str = Field(default="text-embedding-ada-002", alias="EMBEDDING_MODEL")
    openai_max_tokens: int = Field(default=2000, alias="OPENAI_MAX_TOKENS")
    
    # API配置
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_reload: bool = Field(default=True, alias="API_RELOAD")
    api_workers: int = Field(default=1, alias="API_WORKERS")
    
    # 多租户配置
    default_tenant_id: str = Field(
        default="00000000-0000-0000-0000-000000000001", 
        alias="DEFAULT_TENANT_ID"
    )
    enable_rls: bool = Field(default=True, alias="ENABLE_RLS")
    
    # JWT配置
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=1440, alias="JWT_EXPIRATION_MINUTES")
    
    # 在线搜索配置
    serp_api_key: Optional[str] = Field(default=None, alias="SERP_API_KEY")
    google_cse_api_key: Optional[str] = Field(default=None, alias="GOOGLE_CSE_API_KEY")
    google_cse_id: Optional[str] = Field(default=None, alias="GOOGLE_CSE_ID")
    
    # 缓存配置
    enable_llm_cache: bool = Field(default=True, alias="ENABLE_LLM_CACHE")
    llm_cache_ttl: int = Field(default=3600, alias="LLM_CACHE_TTL")
    enable_query_cache: bool = Field(default=True, alias="ENABLE_QUERY_CACHE")
    query_cache_ttl: int = Field(default=600, alias="QUERY_CACHE_TTL")
    
    # 教学配置
    default_teaching_mode: str = Field(default="socratic", alias="DEFAULT_TEACHING_MODE")
    explanation_max_words: int = Field(default=250, alias="EXPLANATION_MAX_WORDS")
    enable_auto_mode_switch: bool = Field(default=True, alias="ENABLE_AUTO_MODE_SWITCH")
    mode_switch_threshold: int = Field(default=3, alias="MODE_SWITCH_THRESHOLD")
    
    # 向量搜索配置
    vector_dimension: int = Field(default=1536, alias="VECTOR_DIMENSION")
    vector_index_lists: int = Field(default=100, alias="VECTOR_INDEX_LISTS")
    vector_top_k: int = Field(default=5, alias="VECTOR_TOP_K")
    
    # Sentry配置
    sentry_dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")
    enable_sentry: bool = Field(default=False, alias="ENABLE_SENTRY")
    
    # 性能监控
    enable_prometheus: bool = Field(default=False, alias="ENABLE_PROMETHEUS")
    prometheus_port: int = Field(default=9090, alias="PROMETHEUS_PORT")
    
    # CORS配置
    enable_cors: bool = Field(default=True, alias="ENABLE_CORS")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"], 
        alias="CORS_ORIGINS"
    )
    enable_api_docs: bool = Field(default=True, alias="ENABLE_API_DOCS")
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v
    
    @field_validator('app_env')
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        """验证应用环境"""
        valid_envs = ["development", "staging", "production"]
        if v not in valid_envs:
            raise ValueError(f"app_env must be one of {valid_envs}")
        return v
    
    @field_validator('default_teaching_mode')
    @classmethod
    def validate_teaching_mode(cls, v: str) -> str:
        """验证教学模式"""
        valid_modes = ["socratic", "lecture", "case_based", "inquiry", "demonstration"]
        if v not in valid_modes:
            raise ValueError(f"default_teaching_mode must be one of {valid_modes}")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 全局配置实例
settings = Settings()
