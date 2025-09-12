import React, { useState } from 'react';
import styled, { keyframes, css } from 'styled-components';
import { colors, gradients, media, skewFadeIn, floatUp } from '../assets/styles/globalStyles';
import Layout from '../components/layout/Layout';
import useAppStore from '../stores/appStore';
import { usePagesTranslation } from '../hooks/useTranslation';

interface CoinPackage {
  id: string;
  coins: number;
  price: number;
  badge?: string;
  pricePerCoin: number;
}

interface PaymentMethod {
  id: string;
  name: string;
  icon: string;
  description?: string;
}

const getPaymentMethods = (t: (key: string) => string): PaymentMethod[] => [
  {
    id: 'card',
    name: t('purchase.paymentMethods.card.name'),
    icon: '💳',
    description: t('purchase.paymentMethods.card.description')
  },
  {
    id: 'paypal',
    name: t('purchase.paymentMethods.paypal.name'),
    icon: '🅿️',
    description: t('purchase.paymentMethods.paypal.description')
  },
  {
    id: 'apple-pay',
    name: t('purchase.paymentMethods.applePay.name'),
    icon: '🍎',
    description: t('purchase.paymentMethods.applePay.description')
  },
  {
    id: 'google-pay',
    name: t('purchase.paymentMethods.googlePay.name'),
    icon: '🟢',
    description: t('purchase.paymentMethods.googlePay.description')
  }
];

const getCoinPackages = (t: (key: string) => string): CoinPackage[] => [
  {
    id: 'small',
    coins: 5,
    price: 1,
    badge: t('purchase.packages.small.badge'),
    pricePerCoin: 1
  },
  {
    id: 'popular',
    coins: 25,
    price: 4,
    badge: t('purchase.packages.popular.badge'),
    pricePerCoin: 0.8
  },
  {
    id: 'best',
    coins: 100,
    price: 10,
    badge: t('purchase.packages.best.badge'),
    pricePerCoin: 0.5
  }
];

const PurchaseContainer = styled.div`
  width: 100%;
  min-height: 100vh;
`;

const glow = keyframes`
  0%, 100% {
    box-shadow: 0 0 20px rgba(212, 175, 55, 0.3);
  }
  50% {
    box-shadow: 0 0 40px rgba(212, 175, 55, 0.6);
  }
`;

const pulse = keyframes`
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
`;

const slideInLeft = keyframes`
  0% {
    opacity: 0;
    transform: translateX(-50px);
  }
  100% {
    opacity: 1;
    transform: translateX(0);
  }
`;

const slideInRight = keyframes`
  0% {
    opacity: 0;
    transform: translateX(50px);
  }
  100% {
    opacity: 1;
    transform: translateX(0);
  }
`;

const PurchaseSection = styled.section`
  padding: 120px 40px 80px;
  background: ${gradients.heroSection};
  min-height: 100vh;
  position: relative;
  overflow: visible;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: none;
    pointer-events: none;
    z-index: 0;
  }

  ${media.tablet} {
    padding: 100px 20px 60px;
  }

  ${media.mobile} {
    padding: 80px 20px 40px;
  }
`;

const PurchaseContent = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 40px;
  align-items: start;
  position: relative;
  z-index: 1;
  overflow: visible;

  ${media.tablet} {
    grid-template-columns: 1fr;
    gap: 30px;
    max-width: 600px;
  }
`;

const LeftSection = styled.div`
  display: flex;
  flex-direction: column;
  animation: ${slideInLeft} 0.8s ease-out;
  overflow: visible;
`;

const PurchaseTitle = styled.h2`
  font-size: 2rem;
  color: ${colors.primary};
  margin-bottom: 15px;
  font-weight: 600;

  ${media.mobile} {
    font-size: 1.8rem;
  }
`;

const PurchaseSubtitle = styled.p`
  font-size: 1rem;
  opacity: 0.8;
  margin-bottom: 30px;
  color: ${colors.white};
`;

const CoinPackagesList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 25px;
  padding: 20px 0;
  overflow: visible;
`;

const CoinPackageItem = styled.div<{ selected?: boolean }>`
  background: linear-gradient(135deg, #2c5aa0 0%, #1e4080 100%);
  border: 2px solid ${props => props.selected ? colors.primary : 'rgba(255, 255, 255, 0.1)'};
  border-radius: 12px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  position: relative;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  overflow: visible;
  animation: ${floatUp} 0.6s ease-out forwards;
  animation-delay: ${props => props.selected ? '0.1s' : '0.3s'};
  opacity: 0;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: none;
    transition: none;
  }

  &:hover {
    transform: translateY(-4px) scale(1.02);
    box-shadow: 0 12px 35px rgba(44, 90, 160, 0.6);
  }

  ${props => props.selected && css`
    border-color: ${colors.primary};
    box-shadow: 0 8px 25px rgba(212, 175, 55, 0.3);
    background: linear-gradient(135deg, #2c5aa0 0%, #1e4080 100%);
  `}
`;

const PackageHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
`;

const CoinCount = styled.div`
  font-size: 1.3rem;
  color: ${colors.white};
  font-weight: 700;
`;

const PackageDetails = styled.div`
  position: absolute;
  top: 20px;
  right: 24px;
  text-align: right;
`;

const PackagePrice = styled.div`
  font-size: 1.6rem;
  color: ${colors.white};
  font-weight: 700;
`;

const PackageBadge = styled.div`
  position: absolute;
  top: -16px;
  left: -16px;
  background: linear-gradient(135deg, ${colors.primary} 0%, #f2d06b 100%);
  color: ${colors.black};
  font-size: 0.75rem;
  font-weight: 700;
  padding: 10px 16px;
  border-radius: 16px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 6px 20px rgba(212, 175, 55, 0.5), 0 0 30px rgba(212, 175, 55, 0.3);
  z-index: 100;
  animation: ${floatUp} 0.8s ease-out 0.5s both, ${pulse} 3s ease-in-out 1s infinite;
  transform: rotate(-8deg);
  
  &::before {
    content: '';
    position: absolute;
    inset: -4px;
    border-radius: 20px;
    background: linear-gradient(135deg, rgba(212, 175, 55, 0.4) 0%, rgba(242, 208, 107, 0.4) 100%);
    z-index: -1;
    animation: ${pulse} 2s ease-in-out infinite;
  }
  
  
  &::before {
    content: '';
    position: absolute;
    inset: -2px;
    border-radius: 12px;
    background: linear-gradient(45deg, ${colors.primary}, #f2d06b, ${colors.primary});
    background-size: 200% 200%;
    z-index: -1;
    opacity: 0.7;
  }
`;

const PackageRate = styled.div`
  position: absolute;
  bottom: 20px;
  left: 24px;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
  font-style: italic;
`;

const RightSection = styled.div`
  position: sticky;
  top: 100px;
  animation: ${slideInRight} 0.8s ease-out;
`;

const PurchaseSummary = styled.div`
  background: linear-gradient(135deg, #1e2749 0%, #2d3748 100%);
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 25px;
  backdrop-filter: blur(15px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  position: relative;
  overflow: hidden;
  transition: all 0.4s ease;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, ${colors.primary}, transparent);
    background-size: 200% 100%;
  }
  
  &::after {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 15px;
    background: linear-gradient(135deg, rgba(212, 175, 55, 0.05) 0%, transparent 50%, rgba(212, 175, 55, 0.02) 100%);
    pointer-events: none;
  }
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
    border-color: rgba(212, 175, 55, 0.3);
  }
`;

const SummaryTitle = styled.h3`
  color: ${colors.primary};
  font-size: 1.4rem;
  margin-bottom: 20px;
  text-align: center;
  font-weight: 600;
`;

const SummaryDetails = styled.div`
  margin-bottom: 25px;
`;

const SummaryRow = styled.div`
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.9);

  &:last-child {
    margin-bottom: 0;
  }

  &.total {
    border-top: 1px solid rgba(255, 255, 255, 0.2);
    padding-top: 12px;
    margin-top: 15px;
    font-size: 1rem;
    font-weight: bold;
    color: ${colors.primary};
  }
`;

const PurchaseBtn = styled.button`
  width: 100%;
  background: ${gradients.primary};
  color: ${colors.black};
  border: none;
  padding: 15px 25px;
  border-radius: 25px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);
  position: relative;
  overflow: hidden;
  z-index: 1;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(
      90deg,
      transparent,
      rgba(255, 255, 255, 0.3),
      transparent
    );
    transition: left 0.6s;
  }
  
  &::after {
    content: '';
    position: absolute;
    inset: -2px;
    border-radius: 25px;
    background: linear-gradient(45deg, ${colors.primary}, #f2d06b, ${colors.primary});
    background-size: 200% 200%;
    z-index: -1;
    opacity: 0;
    transition: opacity 0.4s ease;
  }

  &:hover {
    transform: translateY(-3px) scale(1.02);
    box-shadow: 0 12px 35px rgba(212, 175, 55, 0.5);
    
    &::before {
      left: 100%;
    }
    
    &::after {
      opacity: 1;
    }
  }
  
  &:active {
    transform: translateY(-1px) scale(1.01);
    transition: all 0.1s ease;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
    
    &::before,
    &::after {
      display: none;
    }
  }
`;

const PaymentMethodSection = styled.div`
  margin-bottom: 25px;
`;

const PaymentMethodTitle = styled.h4`
  color: ${colors.primary};
  font-size: 1rem;
  margin-bottom: 15px;
  font-weight: 600;
  text-align: center;
`;

const PaymentMethodGrid = styled.div`
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
`;

const PaymentMethodOption = styled.div<{ selected?: boolean }>`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px 16px;
  border: 2px solid ${props => props.selected ? colors.primary : 'rgba(255, 255, 255, 0.2)'};
  border-radius: 6px;
  background: ${props => props.selected ? 'rgba(212, 175, 55, 0.1)' : 'rgba(255, 255, 255, 0.05)'};
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
  flex: 1;
  min-width: 0;
  
  &:hover {
    border-color: ${colors.primary};
    background: rgba(212, 175, 55, 0.1);
    transform: translateY(-1px);
  }
`;

const PaymentName = styled.div<{ selected?: boolean }>`
  font-size: 0.8rem;
  color: ${props => props.selected ? colors.primary : colors.white};
  font-weight: 600;
  line-height: 1.1;
  transition: color 0.3s ease;
`;

const PolicyAnnouncement = styled.div`
  margin-top: 20px;
  padding: 15px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  border: 1px solid rgba(212, 175, 55, 0.3);

  p {
    font-size: 0.8rem;
    line-height: 1.4;
    color: rgba(255, 255, 255, 0.8);
    margin: 0;
  }

  strong {
    color: ${colors.primary};
  }
`;

const PurchasePage: React.FC = () => {
  const { auth } = useAppStore();
  const { t } = usePagesTranslation();
  const [selectedPackage, setSelectedPackage] = useState<string>('popular');
  const [selectedPayment, setSelectedPayment] = useState<string>('card');
  const currentCoins = 100; // Mock current coins
  
  const paymentMethods = getPaymentMethods(t);
  const coinPackages = getCoinPackages(t);

  const handlePackageSelect = (packageId: string) => {
    setSelectedPackage(packageId);
  };

  const handlePaymentSelect = (paymentId: string) => {
    setSelectedPayment(paymentId);
  };

  const handlePurchase = () => {
    // TODO: Implement actual payment processing
    console.log('Purchase initiated for package:', selectedPackage, 'with payment method:', selectedPayment);
    alert(`${t('purchase.processingPayment')} ${paymentMethods.find(p => p.id === selectedPayment)?.name}. ${t('purchase.demoNotice')}`);
  };

  const getSelectedPackage = () => {
    return coinPackages.find(pkg => pkg.id === selectedPackage) || coinPackages[1];
  };

  const selectedPkg = getSelectedPackage();

  return (
    <Layout>
      <PurchaseContainer>
        <PurchaseSection>
          <PurchaseContent>
            <LeftSection>
              <PurchaseTitle>{t('purchase.title')}</PurchaseTitle>
              <PurchaseSubtitle>
                {t('purchase.subtitle')}
              </PurchaseSubtitle>

              <CoinPackagesList>
                {coinPackages.map((pkg, index) => (
                  <CoinPackageItem
                    key={pkg.id}
                    selected={selectedPackage === pkg.id}
                    onClick={() => handlePackageSelect(pkg.id)}
                    style={{ animationDelay: `${index * 0.2}s` }}
                  >
                    {pkg.badge && <PackageBadge>{pkg.badge}</PackageBadge>}
                    
                    <PackageHeader>
                      <CoinCount>{pkg.coins} {t('purchase.coins')}</CoinCount>
                    </PackageHeader>

                    <PackageDetails>
                      <PackagePrice>${pkg.price}</PackagePrice>
                    </PackageDetails>

                    <PackageRate>${pkg.pricePerCoin.toFixed(2)} / {t('purchase.perTime')}</PackageRate>
                  </CoinPackageItem>
                ))}
              </CoinPackagesList>
            </LeftSection>

            <RightSection>
              <PurchaseSummary>
                <SummaryTitle>{selectedPkg.coins} {t('purchase.coins')}</SummaryTitle>
                
                <SummaryDetails>
                  <SummaryRow>
                    <span>{t('purchase.summary.coinsToReceive')}:</span>
                    <span>{selectedPkg.coins} {t('purchase.coins')}</span>
                  </SummaryRow>
                  <SummaryRow>
                    <span>{t('purchase.summary.coinsAfter')}:</span>
                    <span>{currentCoins + selectedPkg.coins} {t('purchase.coins')}</span>
                  </SummaryRow>
                  <SummaryRow>
                    <span>{t('purchase.summary.currentCoins')}:</span>
                    <span>{currentCoins} {t('purchase.coins')}</span>
                  </SummaryRow>
                  <SummaryRow>
                    <span>{t('purchase.summary.transactionCost')}:</span>
                    <span>${selectedPkg.price}</span>
                  </SummaryRow>
                  <SummaryRow className="total">
                    <span>{t('purchase.summary.coinCurrencyRate')}:</span>
                    <span>${(selectedPkg.price / selectedPkg.coins).toFixed(2)} / {t('purchase.coin')}</span>
                  </SummaryRow>
                </SummaryDetails>

                <PaymentMethodSection>
                  <PaymentMethodTitle>{t('purchase.choosePaymentMethod')}</PaymentMethodTitle>
                  <PaymentMethodGrid>
                    {paymentMethods.map((method) => (
                      <PaymentMethodOption
                        key={method.id}
                        selected={selectedPayment === method.id}
                        onClick={() => handlePaymentSelect(method.id)}
                      >
                        <PaymentName selected={selectedPayment === method.id}>
                          {method.name}
                        </PaymentName>
                      </PaymentMethodOption>
                    ))}
                  </PaymentMethodGrid>
                </PaymentMethodSection>

                <PurchaseBtn onClick={handlePurchase}>
                  {t('purchase.purchaseWith')} {paymentMethods.find(p => p.id === selectedPayment)?.name}
                </PurchaseBtn>

                <PolicyAnnouncement>
                  <p>
                    <strong>{t('purchase.policy.title')}:</strong> {t('purchase.policy.text')}
                  </p>
                </PolicyAnnouncement>
              </PurchaseSummary>
            </RightSection>
          </PurchaseContent>
        </PurchaseSection>
      </PurchaseContainer>
    </Layout>
  );
};

export default PurchasePage;