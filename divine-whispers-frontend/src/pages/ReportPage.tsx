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
  font-size: 1.8rem;
  font-weight: 600;
  margin-bottom: 15px;
  line-height: 1.2;

  ${media.mobile} {
    font-size: 1.4rem;
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
  font-size: 1.3rem;
  font-weight: 600;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;

  ${media.mobile} {
    font-size: 1.1rem;
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
  grid-template-columns: 1fr;
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
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;

  ${media.mobile} {
    font-size: 1rem;
  }
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

const QualityWarning = styled.div`
  background: rgba(255, 193, 7, 0.1);
  border: 1px solid rgba(255, 193, 7, 0.3);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 30px;
  color: #ffc107;
  display: flex;
  align-items: center;
  gap: 12px;
`;

interface QualityIndicatorProps {
  quality: 'high' | 'medium' | 'low';
}

const QualityIndicator = styled.div<QualityIndicatorProps>`
  position: absolute;
  top: 20px;
  right: 20px;
  background: ${props => {
    switch(props.quality) {
      case 'high': return 'rgba(40, 167, 69, 0.2)';
      case 'medium': return 'rgba(255, 193, 7, 0.2)';
      case 'low': return 'rgba(220, 53, 69, 0.2)';
      default: return 'rgba(108, 117, 125, 0.2)';
    }
  }};
  border: 1px solid ${props => {
    switch(props.quality) {
      case 'high': return 'rgba(40, 167, 69, 0.5)';
      case 'medium': return 'rgba(255, 193, 7, 0.5)';
      case 'low': return 'rgba(220, 53, 69, 0.5)';
      default: return 'rgba(108, 117, 125, 0.5)';
    }
  }};
  color: ${props => {
    switch(props.quality) {
      case 'high': return '#28a745';
      case 'medium': return '#ffc107';
      case 'low': return '#dc3545';
      default: return '#6c757d';
    }
  }};
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
  backdrop-filter: blur(10px);

  ${media.mobile} {
    position: static;
    margin: 10px 0;
    align-self: flex-start;
  }
`;

const EmptySection = styled.div`
  background: rgba(108, 117, 125, 0.1);
  border: 1px dashed rgba(108, 117, 125, 0.3);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  color: rgba(255, 255, 255, 0.6);
  font-style: italic;
`;

const IncompleteSection = styled.div`
  background: rgba(220, 53, 69, 0.1);
  border: 1px solid rgba(220, 53, 69, 0.3);
  border-radius: 12px;
  padding: 15px;
  color: #dc3545;
  font-size: 0.9rem;
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const ReportPage: React.FC = () => {
  const { selectedReport, setCurrentPage } = useAppStore();
  const { t } = usePagesTranslation();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  const handleBackClick = () => {
    setCurrentPage('account');
  };

  if (!selectedReport) {
    setCurrentPage('account');
    return null;
  }

  // Calculate report quality and completeness
  const calculateReportQuality = () => {
    const requiredFields = ['LineByLineInterpretation', 'OverallDevelopment', 'PositiveFactors', 'Challenges', 'SuggestedActions', 'SupplementaryNotes', 'Conclusion'];
    const analysis = selectedReport.analysis;

    let emptyFields = 0;
    let shortFields = 0;
    let totalLength = 0;
    const minLengths = {
      'LineByLineInterpretation': 100,
      'OverallDevelopment': 50,
      'PositiveFactors': 50,
      'Challenges': 50,
      'SuggestedActions': 50,
      'SupplementaryNotes': 30,
      'Conclusion': 30
    };

    requiredFields.forEach(field => {
      const content = analysis[field as keyof typeof analysis] || '';
      const cleanContent = content.replace(/\\n/g, '\n').trim();

      if (!cleanContent) {
        emptyFields++;
      } else if (cleanContent.length < (minLengths[field as keyof typeof minLengths] || 30)) {
        shortFields++;
      }
      totalLength += cleanContent.length;
    });

    const completionRate = ((requiredFields.length - emptyFields) / requiredFields.length) * 100;
    const qualityScore = Math.max(0, 100 - (emptyFields * 20) - (shortFields * 10));

    let quality: 'high' | 'medium' | 'low' = 'high';
    if (emptyFields > 0 || qualityScore < 60) quality = 'low';
    else if (shortFields > 2 || qualityScore < 80) quality = 'medium';

    return {
      quality,
      completionRate,
      qualityScore,
      emptyFields,
      shortFields,
      totalLength,
      hasIssues: emptyFields > 0 || shortFields > 2
    };
  };

  const renderSectionContent = (content: string | undefined, sectionName: string, minLength: number = 30) => {
    const cleanContent = content?.replace(/\\n/g, '\n')?.trim() || '';

    if (!cleanContent) {
      return (
        <>
          <EmptySection>
            ⚠️ This section appears to be empty. The report may be incomplete.
          </EmptySection>
          <IncompleteSection>
            🔄 Please try generating a new report for complete analysis
          </IncompleteSection>
        </>
      );
    }

    if (cleanContent.length < minLength) {
      return (
        <>
          <AnalysisContent style={{ whiteSpace: 'pre-wrap' }}>{cleanContent}</AnalysisContent>
          <IncompleteSection>
            ⚠️ This section may be incomplete ({cleanContent.length} characters). Consider regenerating for more detailed analysis.
          </IncompleteSection>
        </>
      );
    }

    return (
      <AnalysisContent style={{ whiteSpace: 'pre-wrap' }}>{cleanContent}</AnalysisContent>
    );
  };

  const reportQuality = calculateReportQuality();

  // Always treat as a regular report

  return (
    <Layout>
      <ReportContainer>
        <ReportSection>
          <ReportContent>
            <BackButton onClick={handleBackClick}>{t('report.backToAccount')}</BackButton>
            
            <ReportCard>
              <QualityIndicator quality={reportQuality.quality}>
                {reportQuality.quality === 'high' && '✅ Complete'}
                {reportQuality.quality === 'medium' && '⚠️ Partial'}
                {reportQuality.quality === 'low' && '❌ Incomplete'}
              </QualityIndicator>

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

              {reportQuality.hasIssues && (
                <QualityWarning>
                  <span>⚠️</span>
                  <div>
                    <strong>Report Quality Notice:</strong> This report may be incomplete.
                    {reportQuality.emptyFields > 0 && `${reportQuality.emptyFields} section(s) are empty. `}
                    {reportQuality.shortFields > 0 && `${reportQuality.shortFields} section(s) may need more detail. `}
                    Consider regenerating for a complete analysis.
                  </div>
                </QualityWarning>
              )}

              <ReportQuestion>
                <QuestionLabel>{t('report.yourQuestion')}</QuestionLabel>
                <QuestionText>"{selectedReport.question}"</QuestionText>
              </ReportQuestion>

              <AnalysisSection>
                <AnalysisTitle>{t('report.lineByLineInterpretation')}</AnalysisTitle>
                {renderSectionContent(selectedReport.analysis.LineByLineInterpretation, 'LineByLineInterpretation', 100)}
              </AnalysisSection>

              <AnalysisSection>
                <AnalysisTitle>{t('report.overallDevelopment')}</AnalysisTitle>
                {renderSectionContent(selectedReport.analysis.OverallDevelopment, 'OverallDevelopment', 50)}
              </AnalysisSection>

              <ElementsList>
                <ElementCard>
                  <ElementTitle>{t('report.positiveFactors')}</ElementTitle>
                  {renderSectionContent(selectedReport.analysis.PositiveFactors, 'PositiveFactors', 50)}
                </ElementCard>

                <ElementCard>
                  <ElementTitle>{t('report.challenges')}</ElementTitle>
                  {renderSectionContent(selectedReport.analysis.Challenges, 'Challenges', 50)}
                </ElementCard>

                <ElementCard>
                  <ElementTitle>{t('report.suggestedActions')}</ElementTitle>
                  {renderSectionContent(selectedReport.analysis.SuggestedActions, 'SuggestedActions', 50)}
                </ElementCard>

                <ElementCard>
                  <ElementTitle>{t('report.supplementaryNotes')}</ElementTitle>
                  {renderSectionContent(selectedReport.analysis.SupplementaryNotes, 'SupplementaryNotes', 30)}
                </ElementCard>

                <ElementCard>
                  <ElementTitle>{t('report.conclusion')}</ElementTitle>
                  {renderSectionContent(selectedReport.analysis.Conclusion, 'Conclusion', 30)}
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
