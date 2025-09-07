import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';
import { colors, gradients, media, skewFadeIn, floatUp } from '../assets/styles/globalStyles';
import Layout from '../components/layout/Layout';
import useAppStore from '../stores/appStore';
import { mockFortunes, mockChatMessages } from '../utils/mockData';

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

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  message: string;
  timestamp: string;
}

const FortuneAnalysisPage: React.FC = () => {
  const { selectedDeity, selectedFortuneNumber, setCurrentPage } = useAppStore();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "msg_001",
      type: "user",
      message: "What does this fortune mean for my career?",
      timestamp: "2024-12-28T15:30:00Z"
    },
    {
      id: "msg_002",
      type: "assistant",
      message: "Your question touches the heart of this divination. The fortune speaks of 'Heaven rewards the diligent' - this is particularly auspicious for career matters. The poem suggests that your hard work and unwavering determination will soon be recognized and rewarded. Consider this a sign that any career moves you're contemplating are divinely supported.",
      timestamp: "2024-12-28T15:30:15Z"
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleBackClick = () => {
    setCurrentPage('fortune-selection');
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const newMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      type: 'user',
      message: inputMessage.trim(),
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, newMessage]);
    setInputMessage('');
    setIsLoading(true);

    // Simulate AI response after a delay
    setTimeout(() => {
      const aiResponse: ChatMessage = {
        id: `msg_${Date.now() + 1}`,
        type: 'assistant',
        message: `Thank you for your question about "${inputMessage.trim()}". Based on this fortune's wisdom, I can offer some insights. The divine message suggests reflection and patience. Consider how this guidance applies to your current situation and trust in the process of spiritual growth.`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, aiResponse]);
      setIsLoading(false);
    }, 2000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (!selectedDeity || !selectedFortuneNumber) {
    setCurrentPage('deities');
    return null;
  }

  // Get fortune data based on selected deity and number
  const fortuneKey = `${selectedDeity.id}_${selectedFortuneNumber}`;
  const fortune = mockFortunes[fortuneKey as keyof typeof mockFortunes] || mockFortunes.guan_yin_7;

  return (
    <Layout>
      <AnalysisContainer>
        <AnalysisSection>
          <AnalysisContent>
            <BackButton onClick={handleBackClick}>
              ← Back to Numbers
            </BackButton>
            
            <FortuneCard>
              {/* Deity Info at the top */}
              <FortuneHeader>
                <DeityInfo>
                  <DeityAvatar 
                    src={`/assets${selectedDeity.imageUrl}`}
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
                  <FortuneLevel>{fortune.fortuneLevel}</FortuneLevel>
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
                  Divine Fortune Reading
                </h1>
                <p style={{ 
                  color: 'rgba(255, 255, 255, 0.8)', 
                  fontSize: '1.1rem',
                  marginBottom: '0'
                }}>
                  Fortune #{selectedFortuneNumber} - {fortune.fortuneLevel}
                </p>
              </div>

              <PoemSection>
                <PoemTitle>Fortune Poem</PoemTitle>
                <PoemText>{fortune.poem}</PoemText>
              </PoemSection>

              <AnalysisTextSection>
                <AnalysisTitle>Divine Interpretation</AnalysisTitle>
                <AnalysisText>{fortune.analysis}</AnalysisText>
              </AnalysisTextSection>
            </FortuneCard>

            <ChatSection>
              <ChatHeader>
                <ChatTitle>Ask for Guidance</ChatTitle>
                <ChatSubtitle>Discuss this fortune with divine wisdom</ChatSubtitle>
              </ChatHeader>
              
              <ChatMessages>
                {messages.map((message) => (
                  <Message key={message.id} isUser={message.type === 'user'}>
                    <MessageBubble isUser={message.type === 'user'}>
                      {message.message}
                    </MessageBubble>
                  </Message>
                ))}
                {isLoading && (
                  <Message isUser={false}>
                    <MessageBubble isUser={false}>
                      Divine wisdom is contemplating your question...
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
                    placeholder="Ask about this fortune..."
                    rows={1}
                  />
                  <SendButton 
                    onClick={handleSendMessage}
                    disabled={!inputMessage.trim() || isLoading}
                  >
                    Send
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