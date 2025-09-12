import React, { useEffect } from 'react';
import styled from 'styled-components';
import { colors, gradients, media, skewFadeIn } from '../assets/styles/globalStyles';
import Layout from '../components/layout/Layout';
import useAppStore from '../stores/appStore';
import { usePagesTranslation } from '../hooks/useTranslation';

const ReportContainer = styled.div`
  width: 100%;
  min-height: 100vh;
  background: ${gradients.background};
`;

const ReportSection = styled.section`
  padding: 120px 40px 80px;
  background: ${gradients.heroSection};

  ${media.tablet} {
    padding: 100px 20px 60px;
  }

  ${media.mobile} {
    padding: 80px 20px 40px;
  }
`;

const ReportContent = styled.div`
  max-width: 900px;
  margin: 0 auto;
  position: relative;
  animation: ${skewFadeIn} 0.6s ease-out;
`;

const BackButton = styled.button`
  background: rgba(212, 175, 55, 0.1);
  border: 2px solid rgba(212, 175, 55, 0.3);
  color: ${colors.primary};
  padding: 12px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s ease;
  backdrop-filter: blur(15px);
  margin-bottom: 30px;

  &:hover {
    background: rgba(212, 175, 55, 0.2);
    border-color: ${colors.primary};
    transform: translateY(-2px);
  }

  ${media.mobile} {
    padding: 10px 16px;
    font-size: 0.9rem;
  }
`;

const ReportCard = styled.div`
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.15) 0%, rgba(212, 175, 55, 0.05) 100%);
  border: 2px solid rgba(212, 175, 55, 0.4);
  border-radius: 20px;
  padding: 40px;
  backdrop-filter: blur(15px);

  ${media.mobile} {
    padding: 30px 20px;
  }
`;

const ReportHeader = styled.div`
  text-align: center;
  margin-bottom: 40px;
  padding-bottom: 30px;
  border-bottom: 1px solid rgba(212, 175, 55, 0.2);
`;

const ReportTitle = styled.h1`
  color: ${colors.primary};
  font-size: 2rem;
  font-weight: 600;
  margin-bottom: 15px;
  line-height: 1.2;

  ${media.mobile} {
    font-size: 1.6rem;
  }
`;

const ReportSubtitle = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;

  ${media.mobile} {
    gap: 15px;
  }
`;

const ReportInfo = styled.span`
  color: rgba(255, 255, 255, 0.8);
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const ReportQuestion = styled.div`
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(212, 175, 55, 0.2);
  border-radius: 15px;
  padding: 25px;
  margin-bottom: 35px;
`;

const QuestionLabel = styled.h3`
  color: ${colors.primary};
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 12px;
`;

const QuestionText = styled.p`
  color: ${colors.white};
  font-size: 1.1rem;
  line-height: 1.6;
  opacity: 0.9;
`;

const AnalysisSection = styled.div`
  margin-bottom: 30px;
`;

const AnalysisTitle = styled.h3`
  color: ${colors.primary};
  font-size: 1.4rem;
  font-weight: 600;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;

  ${media.mobile} {
    font-size: 1.2rem;
  }
`;

const AnalysisContent = styled.div`
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(212, 175, 55, 0.1);
  border-radius: 12px;
  padding: 20px;
  color: ${colors.white};
  line-height: 1.7;
  font-size: 1rem;
  opacity: 0.9;

  ${media.mobile} {
    padding: 15px;
    font-size: 0.95rem;
  }
`;

const ElementsList = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-top: 30px;

  ${media.mobile} {
    grid-template-columns: 1fr;
    gap: 15px;
  }
`;

const ElementCard = styled.div`
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(212, 175, 55, 0.2);
  border-radius: 12px;
  padding: 20px;

  ${media.mobile} {
    padding: 15px;
  }
`;

const ElementTitle = styled.h4`
  color: ${colors.primary};
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const ElementContent = styled.div`
  color: ${colors.white};
  line-height: 1.6;
  font-size: 0.95rem;
  opacity: 0.9;
`;

const TagList = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
`;

const Tag = styled.span`
  background: linear-gradient(135deg, #d4af37 0%, #f4e99b 100%);
  color: ${colors.black};
  padding: 4px 12px;
  border-radius: 15px;
  font-size: 0.85rem;
  font-weight: 500;
`;

const ReportPage: React.FC = () => {
  const { selectedReport, setCurrentPage } = useAppStore();
  const { t } = usePagesTranslation();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  const handleBackClick = () => {
    // If it's the demo report, go back to home page
    if (selectedReport?.id === 'demo_report') {
      setCurrentPage('home');
    } else {
      // For regular reports, go back to account page
      setCurrentPage('account');
    }
  };

  if (!selectedReport) {
    setCurrentPage('account');
    return null;
  }

  // Check if this is the demo report to adjust UI accordingly
  const isDemoReport = selectedReport.id === 'demo_report';

  return (
    <Layout>
      <ReportContainer>
        <ReportSection>
          <ReportContent>
            <BackButton onClick={handleBackClick}>
              {isDemoReport ? t('report.backToHome') : t('report.backToAccount')}
            </BackButton>
            
            <ReportCard>
              <ReportHeader>
                <ReportTitle>{selectedReport.title}</ReportTitle>
                <ReportSubtitle>
                  <ReportInfo>
                    {t('report.deityName', { deity: selectedReport.deity_name })}
                  </ReportInfo>
                  <ReportInfo>
                    {t('report.fortuneNumber', { number: selectedReport.fortune_number })}
                  </ReportInfo>
                  <ReportInfo>
                    {t('report.coinsCost', { cost: selectedReport.cost })}
                  </ReportInfo>
                  <ReportInfo>
                    {t('report.date', { date: new Date(selectedReport.created_at).toLocaleDateString() })}
                  </ReportInfo>
                </ReportSubtitle>
              </ReportHeader>

              <ReportQuestion>
                <QuestionLabel>{t('report.yourQuestion')}</QuestionLabel>
                <QuestionText>"{selectedReport.question}"</QuestionText>
              </ReportQuestion>

              <AnalysisSection>
                <AnalysisTitle>{t('report.divineAnalysisOverview')}</AnalysisTitle>
                <AnalysisContent>{selectedReport.analysis.overview}</AnalysisContent>
              </AnalysisSection>

              <ElementsList>
                <ElementCard>
                  <ElementTitle>{t('report.careerAnalysis')}</ElementTitle>
                  <ElementContent>{selectedReport.analysis.career_analysis}</ElementContent>
                </ElementCard>

                <ElementCard>
                  <ElementTitle>{t('report.relationshipAnalysis')}</ElementTitle>
                  <ElementContent>{selectedReport.analysis.relationship_analysis}</ElementContent>
                </ElementCard>

                <ElementCard>
                  <ElementTitle>{t('report.healthAnalysis')}</ElementTitle>
                  <ElementContent>{selectedReport.analysis.health_analysis}</ElementContent>
                </ElementCard>

                <ElementCard>
                  <ElementTitle>{t('report.luckyElements')}</ElementTitle>
                  <ElementContent>
                    <TagList>
                      {selectedReport.analysis.lucky_elements.map((element, index) => (
                        <Tag key={index}>{element}</Tag>
                      ))}
                    </TagList>
                  </ElementContent>
                </ElementCard>

                <ElementCard>
                  <ElementTitle>{t('report.cautions')}</ElementTitle>
                  <ElementContent>
                    <TagList>
                      {selectedReport.analysis.cautions.map((caution, index) => (
                        <Tag key={index} style={{ 
                          background: 'linear-gradient(135deg, #ff6b6b 0%, #ffa8a8 100%)' 
                        }}>
                          {caution}
                        </Tag>
                      ))}
                    </TagList>
                  </ElementContent>
                </ElementCard>

                <ElementCard style={{ gridColumn: '1 / -1' }}>
                  <ElementTitle>{t('report.divineAdvice')}</ElementTitle>
                  <ElementContent>{selectedReport.analysis.advice}</ElementContent>
                </ElementCard>
              </ElementsList>
            </ReportCard>
          </ReportContent>
        </ReportSection>
      </ReportContainer>
    </Layout>
  );
};

export default ReportPage;