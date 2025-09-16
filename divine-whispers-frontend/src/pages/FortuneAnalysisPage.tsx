import React, { useState, useEffect, useRef } from 'react';
import styled, { keyframes } from 'styled-components';
import { colors, gradients, media, skewFadeIn, floatUp } from '../assets/styles/globalStyles';
import Layout from '../components/layout/Layout';
import useAppStore from '../stores/appStore';
import fortuneService from '../services/fortuneService';
import chatService from '../services/chatService';
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


interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system' | 'report';
  message: string;
  timestamp: string;
  reportId?: string;
}

const FortuneAnalysisPage: React.FC = () => {
  const {
    selectedDeity,
    selectedFortuneNumber,
    setCurrentPage,
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
  const [chatSession, setChatSession] = useState<any>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamHandlersRef = useRef<any>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // useEffect(() => {
  //   scrollToBottom();
  // }, [messages, streamingMessage, isTyping]);

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

  // Initialize chat session and WebSocket when fortune is loaded
  useEffect(() => {
    const initializeChat = async () => {
      if (!fortune || !selectedDeity || !selectedFortuneNumber || !auth.user) return;

      try {
        // Try WebSocket connection first (optional)
        try {
          await chatService.connectWebSocket(auth.user.user_id.toString());
        } catch (wsError) {
          console.warn('WebSocket connection failed, using fallback mode:', wsError);
        }

        // Set up streaming handlers
        streamHandlersRef.current = chatService.setupStreamingHandlers();
        
        streamHandlersRef.current.onChunk((chunk: string) => {
          setStreamingMessage(prev => prev + chunk + ' ');
        });
        
        streamHandlersRef.current.onComplete(() => {
          // Move streaming message to messages and clear
          setMessages(prev => [...prev, {
            id: `msg_${Date.now()}`,
            type: 'assistant',
            message: streamingMessage.trim(),
            timestamp: new Date().toISOString()
          }]);
          setStreamingMessage('');
          setIsTyping(false);
          setIsLoading(false);
        });
        
        streamHandlersRef.current.onTyping((typing: boolean) => {
          setIsTyping(typing);
        });
        
        streamHandlersRef.current.onError((error: string) => {
          console.error('WebSocket streaming error:', error);
          setIsLoading(false);
          setIsTyping(false);
          setStreamingMessage('');
          
          const errorMessage: ChatMessage = {
            id: `msg_${Date.now()}`,
            type: 'system',
            message: 'I apologize, but I am having trouble processing your message right now. Please try again.',
            timestamp: new Date().toISOString()
          };
          setMessages(prev => [...prev, errorMessage]);
        });
        
        // Try to start a fortune conversation (optional)
        try {
          const conversation = await chatService.startFortuneConversation({
            deity_id: selectedDeity.id,
            fortune_number: selectedFortuneNumber,
            initial_question: 'What does this fortune mean for me?',
            context: {
              fortune_id: fortune.id,
              deity_name: selectedDeity.name,
              fortune_number: selectedFortuneNumber
            }
          });
          setChatSession(conversation);
        } catch (conversationError) {
          console.warn('Fortune conversation API failed, using fallback mode:', conversationError);
          setChatSession(null);
        }
        
        // Add initial assistant message
        const initialMessage: ChatMessage = {
          id: 'initial_001',
          type: 'assistant',
          message: `Welcome! I'm here to help you understand the wisdom of ${selectedDeity.name}'s fortune #${selectedFortuneNumber}. Feel free to ask me anything about this divine guidance - its meaning, how it applies to your life, or any specific questions you have.`,
          timestamp: new Date().toISOString()
        };
        
        setMessages([initialMessage]);
        
      } catch (error) {
        console.error('Failed to initialize chat:', error);

        // Always fallback to mock chat if anything fails
        const fallbackMessage: ChatMessage = {
          id: 'fallback_001',
          type: 'assistant',
          message: `I'm here to help you understand the wisdom of ${selectedDeity?.name}'s fortune #${selectedFortuneNumber}. What would you like to know about this divine guidance?`,
          timestamp: new Date().toISOString()
        };

        setMessages([fallbackMessage]);
        setChatSession(null);
      }
    };

    initializeChat();

    // Cleanup on unmount
    return () => {
      if (streamHandlersRef.current) {
        streamHandlersRef.current.cleanup();
        streamHandlersRef.current = null;
      }
      chatService.disconnectWebSocket();
    };
  }, [fortune, selectedDeity, selectedFortuneNumber, auth.user]);

  const handleBackClick = () => {
    setCurrentPage('fortune-selection');
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
    setStreamingMessage(''); // Clear any previous streaming message

    try {
      // If we have a chat session and WebSocket connection, use real-time messaging
      if (chatSession?.session_id) {
        const messagesent = chatService.sendRealtimeMessage(chatSession.session_id, userQuestion);
        
        if (messagesent) {
          // WebSocket message sent successfully
          // Responses will be handled by the streaming handlers
          console.log('Real-time message sent via WebSocket');
          
          // Occasionally offer to generate a report (every 3-4 messages)
          if (messages.length > 0 && (messages.length + 1) % 3 === 0) {
            setTimeout(() => {
              const reportOfferMessage: ChatMessage = {
                id: `msg_${Date.now() + 2}`,
                type: 'system',
                message: `Would you like a detailed personal report based on our conversation? This comprehensive analysis costs 5 coins and includes specific guidance for your situation.`,
                timestamp: new Date().toISOString()
              };
              setMessages(prev => [...prev, reportOfferMessage]);
            }, 3000); // Give more time for AI response to complete
          }
          
          return; // Exit early since WebSocket will handle the response
        } else {
          console.warn('WebSocket not available, falling back to REST API');
        }
      }

      // Fallback to REST API + mock response if WebSocket fails
      try {
        if (chatSession?.session_id) {
          await chatService.sendMessage(chatSession.session_id, userQuestion);
        }
      } catch (error) {
        console.error('Failed to send message via REST API:', error);
      }

      // Get AI response using mock (fallback)
      const aiResponse = await chatService.mockFortuneResponse(
        userQuestion,
        selectedDeity?.id || 'guan_yin',
        selectedFortuneNumber || 7
      );

      const responseMessage: ChatMessage = {
        id: `msg_${Date.now() + 1}`,
        type: 'assistant',
        message: aiResponse,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, responseMessage]);

      // Occasionally offer to generate a report (every 3-4 messages)
      if (messages.length > 0 && (messages.length + 1) % 3 === 0) {
        setTimeout(() => {
          const reportOfferMessage: ChatMessage = {
            id: `msg_${Date.now() + 2}`,
            type: 'system',
            message: `Would you like a detailed personal report based on our conversation? This comprehensive analysis costs 5 coins and includes specific guidance for your situation.`,
            timestamp: new Date().toISOString()
          };
          setMessages(prev => [...prev, reportOfferMessage]);
        }, 1500);
      }

    } catch (error) {
      console.error('Failed to get AI response:', error);
      const errorMessage: ChatMessage = {
        id: `msg_${Date.now() + 1}`,
        type: 'system',
        message: 'I apologize, but I am having trouble processing your message right now. Please try again in a moment.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      // Only set loading to false if we're not using WebSocket (WebSocket handlers will manage this)
      if (!chatService.sendWebSocketMessage({ type: 'ping' })) {
        setIsLoading(false);
      }
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
        overview: `Based on your question "${userQuestion}" and the divine wisdom of ${selectedDeity!.name}, this comprehensive analysis reveals key insights for your path forward.`,
        career_analysis: `Your professional endeavors are blessed with divine guidance. The fortune suggests that your dedication and hard work will soon bear fruit. Trust in your abilities and remain focused on your goals.`,
        relationship_analysis: `In matters of the heart, balance and understanding are key. The divine wisdom suggests that open communication and patience will strengthen your bonds with others.`,
        health_analysis: `Your physical and spiritual well-being require attention. Take time for self-care and meditation to maintain harmony between body and soul.`,
        lucky_elements: ['Water', 'East Direction', 'Green Color', 'Number 7', 'Morning Hours'],
        cautions: ['Avoid hasty decisions', 'Be mindful of negative energy', 'Trust your intuition'],
        advice: `The divine message emphasizes the importance of patience and perseverance. Your question shows wisdom in seeking guidance, and the answer lies within your own inner strength combined with divine blessing.`
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
      setCurrentPage('report');
    }
  };

  if (!selectedDeity || !selectedFortuneNumber) {
    setCurrentPage('deities');
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
                {isLoading && (
                  <Message isUser={false}>
                    <MessageBubble isUser={false}>
                      {t('fortuneAnalysis.generatingReport')}
                    </MessageBubble>
                  </Message>
                )}
                
                {/* Streaming message display */}
                {streamingMessage && (
                  <Message isUser={false}>
                    <MessageBubble isUser={false}>
                      {streamingMessage}
                      <span style={{ opacity: 0.7 }}>▋</span>
                    </MessageBubble>
                  </Message>
                )}
                
                {/* Typing indicator */}
                {isTyping && !streamingMessage && (
                  <Message isUser={false}>
                    <MessageBubble isUser={false}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span>{t('fortuneAnalysis.aiThinking')}</span>
                        <div style={{ display: 'flex', gap: '2px' }}>
                          <div style={{ 
                            width: '6px', 
                            height: '6px', 
                            borderRadius: '50%', 
                            backgroundColor: 'rgba(255, 255, 255, 0.7)',
                            animation: `${pulse} 1.4s ease-in-out infinite both`,
                            animationDelay: '-0.32s'
                          }} />
                          <div style={{ 
                            width: '6px', 
                            height: '6px', 
                            borderRadius: '50%', 
                            backgroundColor: 'rgba(255, 255, 255, 0.7)',
                            animation: `${pulse} 1.4s ease-in-out infinite both`,
                            animationDelay: '-0.16s'
                          }} />
                          <div style={{ 
                            width: '6px', 
                            height: '6px', 
                            borderRadius: '50%', 
                            backgroundColor: 'rgba(255, 255, 255, 0.7)',
                            animation: `${pulse} 1.4s ease-in-out infinite both`
                          }} />
                        </div>
                      </div>
                    </MessageBubble>
                  </Message>
                )}
                
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