-- 为interview_record表添加视频面试相关字段
USE ai_interview;

-- 检查列是否存在，如果不存在则添加
ALTER TABLE interview_record 
ADD COLUMN IF NOT EXISTS is_video_interview BOOLEAN DEFAULT FALSE;

ALTER TABLE interview_record 
ADD COLUMN IF NOT EXISTS video_session_id VARCHAR(200);

ALTER TABLE interview_record 
ADD COLUMN IF NOT EXISTS video_recording_url VARCHAR(500);

ALTER TABLE interview_record 
ADD COLUMN IF NOT EXISTS video_chat_model VARCHAR(100);

-- 显示表结构以验证
DESCRIBE interview_record;