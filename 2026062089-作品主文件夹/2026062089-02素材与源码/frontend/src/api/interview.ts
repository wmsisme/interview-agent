import request from './request'

export interface StartInterviewRequest {
  position: string
  userId?: number
}

export interface StartInterviewResponse {
  interviewId: number
  firstQuestion: string
  firstQuestionId: number
  questionAudioUrl?: string
}

export interface AnswerRequest {
  interviewId: number
  questionId: number
  answerText: string
}

export interface EvaluationResult {
  techScore: number
  depthScore: number
  logicScore: number
  matchScore: number
  feedback: string
  nextQuestion: string
  nextQuestionId?: number
  endInterview: boolean
}

export const startInterview = (position: string, userId?: number) => {
  return request.post<StartInterviewResponse>('/interview/start', {
    position,
    userId
  })
}

export const submitAnswer = (interviewId: number, questionId: number, answerText: string) => {
  return request.post<EvaluationResult>('/interview/answer', {
    interviewId,
    questionId,
    answerText
  })
}

export const submitAudioAnswer = (interviewId: number, questionId: number, audioBlob: Blob) => {
  const formData = new FormData()
  formData.append('interviewId', interviewId.toString())
  formData.append('questionId', questionId.toString())
  formData.append('audio', audioBlob, 'recording.webm')
  return request.post<EvaluationResult>('/interview/answer/audio', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  })
}

export const endInterview = (interviewId: number, conversation?: { role: string; content: string }[]) => {
  return request.post(`/interview/end/${interviewId}`, {
    conversation: conversation || []
  }, {
    timeout: 90000
  })
}

export const saveConversation = (interviewId: number, conversation: { role: string; content: string }[]) => {
  return request.post(`/interview/conversation/${interviewId}`, {
    conversation
  }, {
    timeout: 30000
  })
}

export const getReport = (interviewId: number) => {
  return request.get<string>(`/interview/report/${interviewId}`, {
    timeout: 30000
  })
}

export const downloadReportPdf = (interviewId: number) => {
  return request.get(`/interview/report/pdf/${interviewId}`, {
    responseType: 'blob',
    timeout: 90000
  })
}