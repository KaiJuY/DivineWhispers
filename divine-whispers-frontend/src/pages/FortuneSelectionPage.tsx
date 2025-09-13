import React, { useEffect, useState } from 'react';
import styled from 'styled-components';
import { skewFadeIn, glowing, colors, gradients, media } from '../assets/styles/globalStyles';
import Layout from '../components/layout/Layout';
import useAppStore from '../stores/appStore';
import { usePagesTranslation } from '../hooks/useTranslation';

const FortuneContainer = styled.div`
  width: 100%;
  min-height: 100vh;
`;

const FortuneSection = styled.section`
  padding: 80px 40px;
  background: ${gradients.heroSection};

  ${media.tablet} {
    padding: 60px 20px;
  }

  ${media.mobile} {
    padding: 40px 20px;
  }
`;

const FortuneContent = styled.div`
  max-width: 1400px;
  min-height: 100vh;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
`;

const HeroImage = styled.img`
  width: 100%;
  max-width: 1200px;
  height: 200px;
  object-fit: cover;
  border-radius: 15px;
  margin-bottom: 30px;
  opacity: 0.8;

  ${media.tablet} {
    height: 150px;
    margin-bottom: 25px;
  }

  ${media.mobile} {
    height: 120px;
    margin-bottom: 20px;
  }
`;

const FortuneTitle = styled.h2`
  text-align: center;
  font-size: 3.5rem;
  margin-bottom: 20px;
  color: ${colors.primary};
  font-weight: 300;

  ${media.tablet} {
    font-size: 2.8rem;
    margin-bottom: 15px;
  }

  ${media.mobile} {
    font-size: 2rem;
    margin-bottom: 10px;
  }
`;

const FortuneSubtitle = styled.p`
  text-align: center;
  font-size: 1.2rem;
  margin-bottom: 60px;
  color: ${colors.white};
  opacity: 0.9;

  ${media.tablet} {
    font-size: 1.1rem;
    margin-bottom: 40px;
  }

  ${media.mobile} {
    font-size: 1rem;
    margin-bottom: 30px;
  }
`;


const NumberCard = styled.div<{ isAvailable?: boolean }>`
  aspect-ratio: 1;
  background: ${props => props.isAvailable 
    ? 'linear-gradient(135deg, rgba(212, 175, 55, 0.15) 0%, rgba(212, 175, 55, 0.05) 100%)'
    : 'linear-gradient(135deg, rgba(128, 128, 128, 0.15) 0%, rgba(128, 128, 128, 0.05) 100%)'};
  border: 2px solid ${props => props.isAvailable 
    ? 'rgba(212, 175, 55, 0.4)'
    : 'rgba(128, 128, 128, 0.4)'};
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: ${props => props.isAvailable ? 'pointer' : 'not-allowed'};
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(15px);
  position: relative;
  overflow: hidden;
  animation: ${skewFadeIn} 0.4s ease-out forwards;
  
  &::before {
    content: '';
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    background: linear-gradient(45deg, #d4af37, #f4e99b, #d4af37, #f4e99b);
    background-size: 400% 400%;
    animation: ${glowing} 3s ease-in-out infinite alternate;
    border-radius: inherit;
    z-index: -1;
    opacity: 0;
    transition: opacity 0.4s ease;
  }
  
  &:hover {
    transform: ${props => props.isAvailable ? 'scale(1.15) translateY(-5px)' : 'none'};
    border-color: ${props => props.isAvailable ? '#d4af37' : 'rgba(128, 128, 128, 0.4)'};
    box-shadow: ${props => props.isAvailable ? '0 15px 30px rgba(212, 175, 55, 0.4)' : 'none'};
    z-index: ${props => props.isAvailable ? '10' : '1'};
    color: ${props => props.isAvailable ? '#fff' : 'rgba(128, 128, 128, 0.6)'};
    background: ${props => props.isAvailable 
      ? 'linear-gradient(135deg, #d4af37 0%, #f4e99b 100%)'
      : 'linear-gradient(135deg, rgba(128, 128, 128, 0.15) 0%, rgba(128, 128, 128, 0.05) 100%)'};
  }

  &:hover::before {
    opacity: 1;
  }

  ${media.mobile} {
    border-radius: 6px;
    
    &:hover {
      transform: scale(1.1) translateY(-3px);
    }
  }
`;

const NumbersGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(10, 1fr);
  gap: 15px;
  max-width: 800px;
  width: 100%;

  &:hover ${NumberCard}:not(:hover) {
    opacity: 0.6;
    transform: scale(0.9);
  }

  ${media.tablet} {
    grid-template-columns: repeat(8, 1fr);
    gap: 12px;
  }

  ${media.mobile} {
    grid-template-columns: repeat(5, 1fr);
    gap: 10px;
  }
`;

const NumberText = styled.span<{ isAvailable?: boolean }>`
  font-size: 1.4rem;
  font-weight: 600;
  color: ${props => props.isAvailable ? colors.primary : 'rgba(128, 128, 128, 0.6)'};
  text-shadow: 0 2px 4px rgba(0,0,0,0.5);

  ${media.mobile} {
    font-size: 1.1rem;
  }
`;

const BackButton = styled.button`
  align-self: flex-start;
  background: rgba(212, 175, 55, 0.1);
  border: 2px solid rgba(212, 175, 55, 0.3);
  color: ${colors.primary};
  padding: 12px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s ease;
  backdrop-filter: blur(15px);
  margin-bottom: 20px;

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

const CollectionSection = styled.div`
  margin-bottom: 50px;
  
  &:last-child {
    margin-bottom: 0;
  }
`;

const CollectionHeader = styled.div`
  text-align: center;
  margin-bottom: 30px;
  padding: 20px;
  background: rgba(212, 175, 55, 0.1);
  border: 1px solid rgba(212, 175, 55, 0.3);
  border-radius: 15px;
  backdrop-filter: blur(10px);
`;

const CollectionTitle = styled.h3`
  font-size: 1.8rem;
  color: ${colors.primary};
  margin-bottom: 10px;
  font-weight: 600;
  
  ${media.tablet} {
    font-size: 1.6rem;
  }
  
  ${media.mobile} {
    font-size: 1.4rem;
  }
`;

const CollectionDescription = styled.p`
  color: rgba(255, 255, 255, 0.8);
  font-size: 1rem;
  margin-bottom: 10px;
`;

const CollectionRange = styled.div`
  color: ${colors.primary};
  font-size: 1.1rem;
  font-weight: 500;
`;

const FortuneSelectionPage: React.FC = () => {
  const { selectedDeity, setCurrentPage, setSelectedFortuneNumber, setSelectedCollection } = useAppStore();
  const { t } = usePagesTranslation();
  const [fortuneNumbers, setFortuneNumbers] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Scroll to top when component mounts
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  // Use embedded numbers data from selected deity
  useEffect(() => {
    if (!selectedDeity) {
      setFortuneNumbers(null);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);

      // Use embedded numbers data from the first collection
      const firstCollection = selectedDeity.collections?.[0];
      if (firstCollection && firstCollection.numbers) {
        const numbers = {
          deityId: selectedDeity.id,
          deityName: selectedDeity.name,
          numbers: firstCollection.numbers,
          totalAvailable: firstCollection.numbers.filter(num => num.isAvailable).length
        };
        setFortuneNumbers(numbers);
      } else {
        // Fallback: if no embedded numbers, set to null
        console.warn('No embedded numbers data found for deity:', selectedDeity.name);
        setFortuneNumbers(null);
      }
    } catch (error) {
      console.error('Error processing embedded fortune numbers:', error);
      setFortuneNumbers(null);
    } finally {
      setLoading(false);
    }
  }, [selectedDeity]);

  const handleBackClick = () => {
    setCurrentPage('deities');
  };

  const handleNumberSelect = (number: number, collection: any, isAvailable: boolean) => {
    if (!isAvailable) return; // Prevent selection of unavailable numbers
    
    setSelectedCollection(collection);
    setSelectedFortuneNumber(number);
    setCurrentPage('fortune-analysis');
  };

  if (!selectedDeity) {
    setCurrentPage('deities');
    return null;
  }

  if (loading) {
    return (
      <Layout>
        <FortuneContainer>
          <FortuneSection>
            <FortuneContent>
              <FortuneTitle>Loading Fortune Numbers...</FortuneTitle>
            </FortuneContent>
          </FortuneSection>
        </FortuneContainer>
      </Layout>
    );
  }

  return (
    <Layout>
      <FortuneContainer>
        <FortuneSection>
          <FortuneContent>
            <BackButton onClick={handleBackClick}>
              {t('fortuneSelection.backToDeities')}
            </BackButton>
            <HeroImage 
              src={`${selectedDeity.imageUrl.replace(/\.(jpg|png)$/, '_W.$1')}`} 
              alt={selectedDeity.name}
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.src = '/assets/GuanYin_W.jpg'; // Fallback wide image
              }}
            />
            <FortuneTitle>{t('fortuneSelection.title')}</FortuneTitle>
            <FortuneSubtitle>
              {t('fortuneSelection.subtitle', { deityName: selectedDeity.name })}
            </FortuneSubtitle>
            
            {selectedDeity.collections.map((collection, collectionIndex) => {
              const numbersData = fortuneNumbers?.numbers || [];
              return (
                <CollectionSection key={collection.id}>
                  <CollectionHeader>
                    <CollectionTitle>{collection.name}</CollectionTitle>
                    <CollectionDescription>{collection.description}</CollectionDescription>
                    <CollectionRange>
                      {t('fortuneSelection.numbersRange', { max: collection.maxNumber })}
                      {fortuneNumbers && (
                        <span style={{ display: 'block', marginTop: '5px', fontSize: '0.9rem', opacity: 0.8 }}>
                          Available: {fortuneNumbers.totalAvailable} / {collection.maxNumber}
                        </span>
                      )}
                    </CollectionRange>
                  </CollectionHeader>
                  <NumbersGrid>
                    {numbersData.map((numberData: any, index: number) => (
                      <NumberCard
                        key={`${collection.id}-${numberData.number}`}
                        isAvailable={numberData.isAvailable}
                        style={{ animationDelay: `${(collectionIndex * 100 + index) * 0.005}s` }}
                        onClick={() => handleNumberSelect(numberData.number, collection, numberData.isAvailable)}
                      >
                        <NumberText isAvailable={numberData.isAvailable}>
                          {numberData.number}
                        </NumberText>
                      </NumberCard>
                    ))}
                  </NumbersGrid>
                </CollectionSection>
              );
            })}
          </FortuneContent>
        </FortuneSection>
      </FortuneContainer>
    </Layout>
  );
};

export default FortuneSelectionPage;