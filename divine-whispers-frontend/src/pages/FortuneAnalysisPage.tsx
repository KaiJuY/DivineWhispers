import React, { useState, useEffect, useRef } from 'react';
import styled, { keyframes } from 'styled-components';
import { colors, gradients, media, skewFadeIn, floatUp } from '../assets/styles/globalStyles';
import Layout from '../components/layout/Layout';
import useAppStore from '../stores/appStore';
import { useAppNavigate } from '../contexts/RouterContext';
import fortuneService from '../services/fortuneService';
import { asyncChatService, type TaskProgress, type ChatHistoryItem } from '../services/asyncChatService';
import type { Report } from '../types';
import { usePagesTranslation } from '../hooks/useTranslation';

// Animation for typing indicator
const pulse = keyframes`
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
`;

const AnalysisContainer = styled.div`
  width: 100%;
  min-height: 100vh;
  background: ${gradients.background};
`;

const AnalysisSection = styled.section`
  padding: 120px 40px 80px;
  background: ${gradients.heroSection};

  ${media.tablet} {
    padding: 100px 20px 60px;
  }

  ${media.mobile} {
    padding: 80px 20px 40px;
  }
`;

const AnalysisContent = styled.div`
  max-width: 1400px;
  min-height: 100vh;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 6fr 4fr;
  gap: 40px;
  position: relative;

  ${media.tablet} {
    grid-template-columns: 1fr;
    gap: 30px;
  }

  ${media.mobile} {
    gap: 20px;
  }
`;

const BackButton = styled.button`
  position: absolute;
  top: -60px;
  left: 0;
  background: rgba(212, 175, 55, 0.1);
  border: 2px solid rgba(212, 175, 55, 0.3);
  color: ${colors.primary};
  padding: 12px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s ease;
  backdrop-filter: blur(15px);
  z-index: 10;

  &:hover {
    background: rgba(212, 175, 55, 0.2);
    border-color: ${colors.primary};
    transform: translateY(-2px);
  }

  ${media.mobile} {
    padding: 10px 16px;
    font-size: 0.9rem;
    position: relative;
    top: 0;
    margin-bottom: 20px;
  }
`;

const FortuneCard = styled.div`
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.15) 0%, rgba(212, 175, 55, 0.05) 100%);
  border: 2px solid rgba(212, 175, 55, 0.4);
  border-radius: 20px;
  padding: 40px 30px;
  backdrop-filter: blur(15px);
  animation: ${skewFadeIn} 0.6s ease-out;
  height: 70vh;
  display: flex;
  flex-direction: column;
  overflow-y: auto;

  ${media.mobile} {
    padding: 30px 20px;
    height: auto;
  }
`;

const FortuneHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 30px;
  flex-wrap: wrap;
  gap: 15px;

  ${media.mobile} {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
`;

const DeityInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 15px;

  ${media.mobile} {
    gap: 10px;
  }
`;

const DeityAvatar = styled.img`
  width: 60px;
  height: 60px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid rgba(212, 175, 55, 0.5);

  ${media.mobile} {
    width: 50px;
    height: 50px;
  }
`;

const DeityName = styled.h3`
  color: ${colors.primary};
  font-size: 1.5rem;
  font-weight: 600;

  ${media.mobile} {
    font-size: 1.3rem;
  }
`;

const FortuneNumber = styled.div`
  background: linear-gradient(135deg, #d4af37 0%, #f4e99b 100%);
  color: ${colors.black};
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: bold;
  font-size: 1.1rem;

  ${media.mobile} {
    font-size: 1rem;
    padding: 6px 12px;
  }
`;

const FortuneLevel = styled.span`
  color: ${colors.primary};
  font-size: 1.2rem;
  font-weight: 600;

  ${media.mobile} {
    font-size: 1.1rem;
  }
`;

const PoemSection = styled.div`
  margin-bottom: 30px;
`;

const PoemTitle = styled.h4`
  color: ${colors.primary};
  font-size: 1.3rem;
  margin-bottom: 15px;
  font-weight: 500;

  ${media.mobile} {
    font-size: 1.2rem;
  }
`;

const PoemText = styled.div`
  background: rgba(0, 0, 0, 0.3);
  padding: 20px;
  border-radius: 12px;
  border: 1px solid rgba(212, 175, 55, 0.2);
  line-height: 1.8;
  font-size: 1.1rem;
  color: ${colors.white};
  white-space: pre-line;
  text-align: center;
  font-family: 'Georgia', serif;

  ${media.mobile} {
    padding: 15px;
    font-size: 1rem;
  }
`;

const AnalysisTextSection = styled.div``;

const AnalysisTitle = styled.h4`
  color: ${colors.primary};
  font-size: 1.3rem;
  margin-bottom: 15px;
  font-weight: 500;

  ${media.mobile} {
    font-size: 1.2rem;
  }
`;

const AnalysisText = styled.p`
  color: ${colors.white};
  line-height: 1.7;
  font-size: 1rem;
  opacity: 0.9;

  ${media.mobile} {
    font-size: 0.95rem;
  }
`;

const ChatSection = styled.div`
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.1) 0%, rgba(212, 175, 55, 0.05) 100%);
  border: 2px solid rgba(212, 175, 55, 0.3);
  border-radius: 20px;
  backdrop-filter: blur(15px);
  animation: ${floatUp} 0.6s ease-out 0.3s both;
  height: 70vh;
  display: flex;
  flex-direction: column;

  ${media.tablet} {
    order: -1;
    height: auto;
  }
`;

const ChatHeader = styled.div`
  padding: 20px 25px;
  border-bottom: 1px solid rgba(212, 175, 55, 0.2);

  ${media.mobile} {
    padding: 15px 20px;
  }
`;

const ChatTitle = styled.h3`
  color: ${colors.primary};
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 5px;

  ${media.mobile} {
    font-size: 1.1rem;
  }
`;

const ChatSubtitle = styled.p`
  color: ${colors.white};
  opacity: 0.7;
  font-size: 0.9rem;
`;

const ChatMessages = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 20px 25px;
  display: flex;
  flex-direction: column;
  gap: 15px;
  min-height: 0;

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: rgba(10, 17, 40, 0.3);
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #d4af37 0%, #f4e99b 100%);
    border-radius: 3px;
  }

  ${media.mobile} {
    padding: 15px 20px;
  }
`;

const Message = styled.div<{ isUser: boolean }>`
  display: flex;
  justify-content: ${props => props.isUser ? 'flex-end' : 'flex-start'};
`;

const MessageBubble = styled.div<{ isUser: boolean }>`
  max-width: 85%;
  padding: 12px 16px;
  border-radius: ${props => props.isUser ? '18px 18px 5px 18px' : '18px 18px 18px 5px'};
  background: ${props => props.isUser 
    ? 'linear-gradient(135deg, #d4af37 0%, #f4e99b 100%)' 
    : 'rgba(212, 175, 55, 0.15)'};
  color: ${props => props.isUser ? colors.black : colors.white};
  border: 1px solid ${props => props.isUser ? 'transparent' : 'rgba(212, 175, 55, 0.3)'};
  line-height: 1.5;
  font-size: 0.95rem;

  ${media.mobile} {
    max-width: 90%;
    font-size: 0.9rem;
    padding: 10px 14px;
  }
`;

const ChatInputSection = styled.div`
  padding: 20px 25px;
  border-top: 1px solid rgba(212, 175, 55, 0.2);

  ${media.mobile} {
    padding: 15px 20px;
  }
`;

const ChatInputContainer = styled.div`
  display: flex;
  gap: 10px;
  align-items: flex-end;
`;

const ChatInput = styled.textarea`
  flex: 1;
  background: rgba(0, 0, 0, 0.3);
  border: 2px solid rgba(212, 175, 55, 0.3);
  border-radius: 12px;
  padding: 12px 16px;
  color: ${colors.white};
  font-size: 0.95rem;
  line-height: 1.4;
  resize: none;
  min-height: 40px;
  max-height: 120px;
  transition: all 0.3s ease;

  &:focus {
    outline: none;
    border-color: ${colors.primary};
    background: rgba(0, 0, 0, 0.5);
  }

  &::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }

  ${media.mobile} {
    font-size: 0.9rem;
    padding: 10px 12px;
  }
`;

const SendButton = styled.button`
  background: linear-gradient(135deg, #d4af37 0%, #f4e99b 100%);
  border: none;
  border-radius: 10px;
  padding: 12px 20px;
  color: ${colors.black};
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(212, 175, 55, 0.3);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }

  ${media.mobile} {
    padding: 10px 16px;
    font-size: 0.9rem;
  }
`;

const ReportMessage = styled.div`
  background: linear-gradient(135deg, rgba(100, 200, 100, 0.2) 0%, rgba(50, 150, 50, 0.1) 100%);
  border: 2px solid rgba(100, 200, 100, 0.4);
  border-radius: 15px;
  padding: 15px 20px;
  margin: 10px 0;
  display: flex;
  flex-direction: column;
  gap: 15px;
`;

const ReportHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
`;

const ReportTitle = styled.span`
  color: rgba(100, 255, 100, 0.9);
  font-weight: 600;
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const ReportButton = styled.button`
  background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
  color: ${colors.black};
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(34, 197, 94, 0.3);
  }
`;

const ProgressBar = styled.div<{ progress: number }>`
  width: 100%;
  height: 6px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 3px;
  overflow: hidden;
  margin-top: 8px;

  &::after {
    content: '';
    display: block;
    width: ${props => props.progress}%;
    height: 100%;
    background: linear-gradient(135deg, #d4af37 0%, #f4e99b 100%);
    transition: width 0.3s ease;
  }
`;

const ProgressMessage = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.8);
`;


interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system' | 'report' | 'progress';
  message: string;
  timestamp: string;
  reportId?: string;
  progress?: number;
  status?: string;
  reportOfferQuestion?: string;
}

const FortuneAnalysisPage: React.FC = () => {
  const navigate = useAppNavigate();
  const {
    selectedDeity,
    selectedFortuneNumber,
    userCoins,
    setUserCoins,
    reports,
    setReports,
    setSelectedReport,
    auth,
    currentLanguage
  } = useAppStore();
  const { t } = usePagesTranslation();
  const [fortune, setFortune] = useState<any>(null);

  // Helper function to get analysis text in current language
  const getAnalysisText = (fortune: any) => {
    if (!fortune?.poem?.analysis) return '';

    const analysis = fortune.poem.analysis;

    // Try to get analysis in current language
    if (analysis[currentLanguage]) {
      return analysis[currentLanguage];
    }

    // Fallback to available languages in order: zh > en > jp
    if (analysis.zh) return analysis.zh;
    if (analysis.en) return analysis.en;
    if (analysis.jp) return analysis.jp;

    // If analysis is a string (legacy format), return as-is
    if (typeof analysis === 'string') return analysis;

    return '';
  };
  const [fortuneLoading, setFortuneLoading] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const sseCleanupRef = useRef<(() => void) | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // useEffect(() => {
  //   scrollToBottom();
  // }, [messages]);

  // Scroll to top when component mounts
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  // Fetch fortune data when component mounts
  useEffect(() => {
    const fetchFortune = async () => {
      if (!selectedDeity || !selectedFortuneNumber) return;

      try {
        setFortuneLoading(true);
        const fortuneData = await fortuneService.getFortuneByDeityAndNumber(
          selectedDeity.id,
          selectedFortuneNumber
        );
        setFortune(fortuneData);
      } catch (error) {
        console.error('Failed to fetch fortune:', error);
      } finally {
        setFortuneLoading(false);
      }
    };

    fetchFortune();
  }, [selectedDeity, selectedFortuneNumber]);

  // Initialize chat when fortune is loaded
  useEffect(() => {
    const initializeChat = () => {
      if (!fortune || !selectedDeity || !selectedFortuneNumber || !auth.user) return;

      // Add initial assistant message
      const initialMessage: ChatMessage = {
        id: 'initial_001',
        type: 'assistant',
        message: `Welcome! I'm here to help you understand the wisdom of ${selectedDeity.name}'s fortune #${selectedFortuneNumber}. Feel free to ask me anything about this divine guidance - its meaning, how it applies to your life, or any specific questions you have.`,
        timestamp: new Date().toISOString()
      };

      setMessages([initialMessage]);
    };

    initializeChat();

    // Cleanup on unmount
    return () => {
      if (sseCleanupRef.current) {
        sseCleanupRef.current();
        sseCleanupRef.current = null;
      }
    };
  }, [fortune, selectedDeity, selectedFortuneNumber, auth.user]);

  const handleBackClick = () => {
    navigate('/fortune-selection');
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userQuestion = inputMessage.trim();
    const newMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      type: 'user',
      message: userQuestion,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, newMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // Submit question to async chat service
      const taskResponse = await asyncChatService.askQuestion({
        deity_id: selectedDeity!.id,
        fortune_number: selectedFortuneNumber!,
        question: userQuestion,
        context: {
          fortune_id: fortune.id,
          deity_name: selectedDeity!.name
        }
      });

      setCurrentTaskId(taskResponse.task_id);

      // Add progress tracking message
      const progressMessage: ChatMessage = {
        id: `progress_${taskResponse.task_id}`,
        type: 'progress',
        message: taskResponse.message,
        timestamp: new Date().toISOString(),
        status: taskResponse.status,
        progress: 0
      };

      setMessages(prev => [...prev, progressMessage]);

      // Subscribe to progress updates via SSE
      const cleanup = asyncChatService.subscribeToProgress(
        taskResponse.task_id,
        (progressData: TaskProgress) => {
          if (progressData.type === 'progress') {
            // Update progress message
            setMessages(prev => prev.map(msg =>
              msg.id === `progress_${taskResponse.task_id}`
                ? { ...msg, message: progressData.message || 'Processing...', progress: progressData.progress }
                : msg
            ));
          } else if (progressData.type === 'complete' && progressData.result) {
            // Remove the progress message
            setMessages(prev => prev.filter(msg => msg.id !== `progress_${taskResponse.task_id}`));

            let structuredReportHandled = false;
            // Try to parse structured JSON report from response first (robust)
            try {
              const raw = progressData.result.response || '';

              const parseMaybeJson = (text: string): any => {
                // 1) Try direct parse
                try {
                  const direct = JSON.parse(text);
                  // If it parsed to a string, try to parse that string again (double-encoded JSON)
                  if (typeof direct === 'string') {
                    try { return JSON.parse(direct); } catch {}
                  }
                  return direct;
                } catch {}

                // 2) Strip markdown code fences
                let cleaned = text.trim();
                if (cleaned.startsWith('```')) {
                  const firstBrace = cleaned.indexOf('{');
                  const lastBrace = cleaned.lastIndexOf('}');
                  if (firstBrace !== -1 && lastBrace !== -1 && lastBrace > firstBrace) {
                    cleaned = cleaned.slice(firstBrace, lastBrace + 1);
                  }
                }

                // 3) Extract first JSON object block
                const match = cleaned.match(/\{[\s\S]*\}/);
                if (match) {
                  try { return JSON.parse(match[0]); } catch {}
                }
                return null;
              };

              const parsedRaw = parseMaybeJson(raw) as any;
              // Fuzzy map keys by first 3 letters (lowercased, alpha-only)
              const canonMap: Record<string, string> = {
                lin: 'LineByLineInterpretation',
                ove: 'OverallDevelopment',
                pos: 'PositiveFactors',
                cha: 'Challenges',
                sug: 'SuggestedActions',
                sup: 'SupplementaryNotes',
                con: 'Conclusion',
              };
              const normalizeKeys = (obj: any) => {
                const out: any = {};
                if (obj && typeof obj === 'object') {
                  for (const [k, v] of Object.entries(obj)) {
                    const nk = String(k).toLowerCase().replace(/[^a-z]/g, '');
                    const pref = nk.slice(0, 3) as keyof typeof canonMap;
                    const mapped = (canonMap as any)[pref] || null;
                    if (mapped) out[mapped] = String(v);
                    else out[k] = v as any;
                  }
                }
                return out;
              };

              const parsed = normalizeKeys(parsedRaw);
              const requiredKeys = [
                'LineByLineInterpretation',
                'OverallDevelopment',
                'PositiveFactors',
                'Challenges',
                'SuggestedActions',
                'SupplementaryNotes',
                'Conclusion'
              ];
              const hasAny = parsed && requiredKeys.some(k => typeof parsed?.[k] === 'string');
              if (hasAny && selectedDeity && selectedFortuneNumber) {
                const reportId = `report_${Date.now()}`;
                const newReport: Report = {
                  id: reportId,
                  title: `Personal Reading Report`,
                  question: inputMessage || '',
                  deity_id: selectedDeity.id,
                  deity_name: selectedDeity.name,
                  fortune_number: selectedFortuneNumber,
                  cost: 0,
                  status: 'completed',
                  created_at: new Date().toISOString(),
                  analysis: {
                    LineByLineInterpretation: parsed.LineByLineInterpretation || '',
                    OverallDevelopment: parsed.OverallDevelopment || '',
                    PositiveFactors: parsed.PositiveFactors || '',
                    Challenges: parsed.Challenges || '',
                    SuggestedActions: parsed.SuggestedActions || '',
                    SupplementaryNotes: parsed.SupplementaryNotes || '',
                    Conclusion: parsed.Conclusion || ''
                  }
                };
                // Save report (store function expects full array, not an updater)
                setReports([...reports, newReport]);

                // Add a concise completion status message (no raw JSON)
                const statusMessage: ChatMessage = {
                  id: `msg_${Date.now()}`,
                  type: 'assistant',
                  message: parsed.Conclusion || 'Analysis complete. Your detailed report is ready.',
                  timestamp: new Date().toISOString()
                };
                setMessages(prev => [...prev, statusMessage]);

                // Add report link card
                const reportMessage: ChatMessage = {
                  id: `msg_${Date.now() + 1}`,
                  type: 'report',
                  message: 'Your detailed report is ready. View now?',
                  timestamp: new Date().toISOString(),
                  reportId
                };
                setMessages(prev => [...prev, reportMessage]);

                structuredReportHandled = true;
              }
            } catch {}

            // Fallback: if not structured JSON, show regular assistant text
            if (!structuredReportHandled) {
              const responseMessage: ChatMessage = {
                id: `msg_${Date.now()}`,
                type: 'assistant',
                message: progressData.result.response,
                timestamp: new Date().toISOString()
              };
              setMessages(prev => [...prev, responseMessage]);

              // Offer to generate a report in fallback mode (always when allowed)
              if (progressData.result.can_generate_report) {
                setMessages(prev => {
                  const lastUser = [...prev].reverse().find(m => m.type === 'user');
                  const userQ = lastUser?.message || '';
                  const reportOfferMessage: ChatMessage = {
                    id: `msg_${Date.now() + 1}`,
                    type: 'system',
                    message: `Would you like a detailed personal report based on our conversation? This comprehensive analysis costs 5 coins and includes specific guidance for your situation.`,
                    timestamp: new Date().toISOString(),
                    reportOfferQuestion: userQ
                  };
                  return [...prev, reportOfferMessage];
                });
              }
            }

            setIsLoading(false);
            setCurrentTaskId(null);
          } else if (progressData.type === 'error') {
            // Remove progress message and add error
            setMessages(prev => prev.filter(msg => msg.id !== `progress_${taskResponse.task_id}`));

            const errorMessage: ChatMessage = {
              id: `msg_${Date.now()}`,
              type: 'system',
              message: progressData.error || 'Failed to process your message. Please try again.',
              timestamp: new Date().toISOString()
            };

            setMessages(prev => [...prev, errorMessage]);
            setIsLoading(false);
            setCurrentTaskId(null);
          }
        },
        (error) => {
          console.error('SSE error:', error);
          setIsLoading(false);
          setCurrentTaskId(null);

          const errorMessage: ChatMessage = {
            id: `msg_${Date.now()}`,
            type: 'system',
            message: 'Connection lost. Please try again.',
            timestamp: new Date().toISOString()
          };
          setMessages(prev => [...prev, errorMessage]);
        }
      );

      // Store cleanup function
      sseCleanupRef.current = cleanup;

    } catch (error) {
      console.error('Failed to submit question:', error);
      setIsLoading(false);

      const errorMessage: ChatMessage = {
        id: `msg_${Date.now()}`,
        type: 'system',
        message: error instanceof Error ? error.message : 'Failed to submit your question. Please try again.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  // Handle report generation when user requests it
  const handleGenerateReport = async (userQuestion: string) => {
    if (userCoins < 5) {
      const insufficientCoinsResponse: ChatMessage = {
        id: `msg_${Date.now()}`,
        type: 'system',
        message: t('fortuneAnalysis.insufficientCoins'),
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, insufficientCoinsResponse]);
      return;
    }

    // Create a new report
    const reportId = `report_${Date.now()}`;
    const newReport: Report = {
      id: reportId,
      title: `Personal Reading Report`,
      question: userQuestion,
      deity_id: selectedDeity!.id,
      deity_name: selectedDeity!.name,
      fortune_number: selectedFortuneNumber!,
      cost: 5,
      status: 'completed',
      created_at: new Date().toISOString(),
      analysis: {
        LineByLineInterpretation: `[Line-by-Line | ${selectedDeity!.name} #${selectedFortuneNumber!}]\n1) Imagery mapping: how each line reflects your situation.\n2) Context linkage: connect poem phrases to your question.\n3) Transformation cue: practical mindset and action adjustments.`,
        OverallDevelopment: `Based on your question "${userQuestion}" and the divine wisdom of ${selectedDeity!.name}, your current situation is stabilizing with a gradual positive trend. Short-term progress appears steady, with longer-term development favored by consistent effort and clear intentions.`,
        PositiveFactors: `Support from kind people and mentors, opportunities through collaboration, and your persistence strengthen outcomes. Clear communication and maintaining balance draw favorable conditions.`,
        Challenges: `Avoid rushing or overcommitting. Emotional fluctuations and external distractions can slow progress. Be mindful of overthinking and self-doubt during key decisions.`,
        SuggestedActions: `Set achievable milestones, communicate openly, and practice patience. Maintain steady routines, take restorative breaks, and trust your intuition while verifying details before acting.`,
        SupplementaryNotes: `If about career, focus on teamwork and mentorship. If about relationships, practice empathy and calm dialogue. For health, prioritize rest and gentle movement. For finances, proceed conservatively and avoid speculation.`,
        Conclusion: `Stay patient and centered—the opportunity is near. Keep moving forward step by step; progress will come.`
      }
    };

    // Add report to store
    setReports([...reports, newReport]);

    // Deduct coins
    setUserCoins(userCoins - 5);

    // Send report message
    const reportMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      type: 'report',
      message: t('fortuneAnalysis.reportMessage'),
      timestamp: new Date().toISOString(),
      reportId: reportId
    };

    setMessages(prev => [...prev, reportMessage]);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleViewReport = (reportId: string) => {
    const report = reports.find(r => r.id === reportId);
    if (report) {
      setSelectedReport(report);
      navigate('/report');
    }
  };

  if (!selectedDeity || !selectedFortuneNumber) {
    navigate('/deities');
    return null;
  }

  if (fortuneLoading) {
    return (
      <Layout>
        <AnalysisContainer>
          <AnalysisSection>
            <AnalysisContent>
              <div style={{ textAlign: 'center', color: colors.primary, fontSize: '2rem' }}>
                Loading Your Fortune...
              </div>
            </AnalysisContent>
          </AnalysisSection>
        </AnalysisContainer>
      </Layout>
    );
  }

  if (!fortune) {
    return (
      <Layout>
        <AnalysisContainer>
          <AnalysisSection>
            <AnalysisContent>
              <div style={{ textAlign: 'center', color: colors.primary, fontSize: '1.5rem' }}>
                Fortune not found. Please try selecting a different number.
              </div>
              <BackButton onClick={handleBackClick} style={{ margin: '20px auto', position: 'relative', top: 'auto' }}>
                {t('fortuneAnalysis.backToNumbers')}
              </BackButton>
            </AnalysisContent>
          </AnalysisSection>
        </AnalysisContainer>
      </Layout>
    );
  }

  return (
    <Layout>
      <AnalysisContainer>
        <AnalysisSection>
          <AnalysisContent>
            <BackButton onClick={handleBackClick}>
              {t('fortuneAnalysis.backToNumbers')}
            </BackButton>

            <FortuneCard>
              {/* Deity Info at the top */}
              <FortuneHeader>
                <DeityInfo>
                  <DeityAvatar
                    src={`${selectedDeity.imageUrl}`}
                    alt={selectedDeity.name}
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.src = '/assets/GuanYin.jpg'; // Fallback image
                    }}
                  />
                  <DeityName>{selectedDeity.name}</DeityName>
                </DeityInfo>
                <div style={{ display: 'flex', alignItems: 'center', gap: '15px', flexWrap: 'wrap' }}>
                  <FortuneNumber>#{selectedFortuneNumber}</FortuneNumber>
                  <FortuneLevel>{fortune.poem?.fortune || fortune.fortuneLevel || ''}</FortuneLevel>
                </div>
              </FortuneHeader>

              {/* Main Title and Subtitle */}
              <div style={{ textAlign: 'center', marginBottom: '30px', marginTop: '20px' }}>
                <h1 style={{
                  color: '#d4af37',
                  fontSize: '2rem',
                  fontWeight: '600',
                  marginBottom: '10px',
                  lineHeight: '1.2'
                }}>
                  {t('fortuneAnalysis.title')}
                </h1>
                <p style={{
                  color: 'rgba(255, 255, 255, 0.8)',
                  fontSize: '1.1rem',
                  marginBottom: '0'
                }}>
                  {t('fortuneAnalysis.subtitle', { number: selectedFortuneNumber, fortuneLevel: fortune.poem?.fortune || fortune.fortuneLevel || '' })}
                </p>
              </div>

              <PoemSection>
                <PoemTitle>{t('fortuneAnalysis.poemTitle')}</PoemTitle>
                <PoemText>{fortune.poem?.poem || ''}</PoemText>
              </PoemSection>

              <AnalysisTextSection>
                <AnalysisTitle>{t('fortuneAnalysis.analysisTitle')}</AnalysisTitle>
                <AnalysisText>{getAnalysisText(fortune)}</AnalysisText>
              </AnalysisTextSection>
            </FortuneCard>

              <ChatSection>
              <ChatHeader>
                <ChatTitle>{t('fortuneAnalysis.chatTitle')}</ChatTitle>
                <ChatSubtitle>{t('fortuneAnalysis.chatSubtitle')}</ChatSubtitle>
              </ChatHeader>
              
              <ChatMessages>
                {messages.map((message) => {
                  if (message.type === 'report') {
                    return (
                      <div key={message.id}>
                        <ReportMessage>
                          <ReportHeader>
                            <ReportTitle>
                              {t('fortuneAnalysis.reportGenerated')}
                            </ReportTitle>
                            <ReportButton onClick={() => handleViewReport(message.reportId!)}>
                              {t('fortuneAnalysis.viewReportButton')}
                            </ReportButton>
                          </ReportHeader>
                          <div style={{ color: 'rgba(255, 255, 255, 0.9)' }}>
                            {message.message}
                          </div>
                        </ReportMessage>
                      </div>
                    );
                  }

                  // Offer card to generate a report
                  if (message.type === 'system' && message.reportOfferQuestion) {
                    return (
                      <div key={message.id}>
                        <ReportMessage>
                          <ReportHeader>
                            <ReportTitle>
                              {t('fortuneAnalysis.reportOfferTitle', { defaultValue: 'Personal Report Offer' })}
                            </ReportTitle>
                            <ReportButton onClick={() => handleGenerateReport(message.reportOfferQuestion!)}>
                              {t('fortuneAnalysis.generateReport', { defaultValue: 'Generate Report' })}
                            </ReportButton>
                          </ReportHeader>
                          <div style={{ color: 'rgba(255, 255, 255, 0.9)' }}>
                            {message.message}
                          </div>
                        </ReportMessage>
                      </div>
                    );
                  }

                  if (message.type === 'progress') {
                    return (
                      <Message key={message.id} isUser={false}>
                        <MessageBubble
                          isUser={false}
                          style={{
                            background: 'linear-gradient(135deg, rgba(212, 175, 55, 0.2) 0%, rgba(212, 175, 55, 0.1) 100%)',
                            border: '2px solid rgba(212, 175, 55, 0.4)'
                          }}
                        >
                          <ProgressMessage>
                            <span>{message.message}</span>
                            <ProgressBar progress={message.progress || 0} />
                            <small style={{ opacity: 0.7 }}>
                              {message.status === 'analyzing_rag' && 'Analyzing fortune context...'}
                              {message.status === 'generating_llm' && 'Consulting divine wisdom...'}
                              {message.status === 'processing' && 'Processing your question...'}
                              {!message.status && 'Preparing response...'}
                            </small>
                          </ProgressMessage>
                        </MessageBubble>
                      </Message>
                    );
                  }

                  return (
                    <Message key={message.id} isUser={message.type === 'user'}>
                      <MessageBubble
                        isUser={message.type === 'user'}
                        style={message.type === 'system' ? {
                          background: 'linear-gradient(135deg, rgba(255, 100, 100, 0.2) 0%, rgba(200, 50, 50, 0.1) 100%)',
                          border: '2px solid rgba(255, 100, 100, 0.4)',
                          color: 'rgba(255, 200, 200, 0.9)'
                        } : {}}
                      >
                        {message.message}
                      </MessageBubble>
                    </Message>
                  );
                })}
                <div ref={messagesEndRef} />
              </ChatMessages>

              <ChatInputSection>
                <ChatInputContainer>
                  <ChatInput
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder={t('fortuneAnalysis.chatPlaceholder')}
                    rows={1}
                  />
                  <SendButton 
                    onClick={handleSendMessage}
                    disabled={!inputMessage.trim() || isLoading}
                  >
                    {t('fortuneAnalysis.sendButton')}
                  </SendButton>
                </ChatInputContainer>
              </ChatInputSection>
            </ChatSection>
          </AnalysisContent>
        </AnalysisSection>
      </AnalysisContainer>
    </Layout>
  );
};

export default FortuneAnalysisPage;
