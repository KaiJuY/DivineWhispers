import styled, { createGlobalStyle, keyframes, css } from 'styled-components';

// Global keyframes
export const glow = keyframes`
  0% { 
    text-shadow: 
      0 0 10px rgba(212, 175, 55, 0.3), 
      0 0 20px rgba(212, 175, 55, 0.2), 
      2px 2px 4px rgba(0, 0, 0, 0.8); 
  }
  100% { 
    text-shadow: 
      0 0 15px rgba(212, 175, 55, 0.5), 
      0 0 30px rgba(212, 175, 55, 0.3), 
      2px 2px 4px rgba(0, 0, 0, 0.8); 
  }
`;

export const breathe = keyframes`
  0%, 100% { 
    transform: scale(0.98);
    filter: drop-shadow(0 0 8px rgba(212, 175, 55, 0.3));
  }
  10% {
    transform: scale(0.99);
    filter: drop-shadow(0 0 10px rgba(212, 175, 55, 0.35));
  }
  20% {
    transform: scale(1);
    filter: drop-shadow(0 0 12px rgba(212, 175, 55, 0.4));
  }
  30% {
    transform: scale(1.01);
    filter: drop-shadow(0 0 14px rgba(212, 175, 55, 0.5));
  }
  40% {
    transform: scale(1.02);
    filter: drop-shadow(0 0 16px rgba(212, 175, 55, 0.6));
  }
  50% { 
    transform: scale(1.03);
    filter: drop-shadow(0 0 18px rgba(212, 175, 55, 0.7));
  }
  60% {
    transform: scale(1.02);
    filter: drop-shadow(0 0 16px rgba(212, 175, 55, 0.6));
  }
  70% {
    transform: scale(1.01);
    filter: drop-shadow(0 0 14px rgba(212, 175, 55, 0.5));
  }
  80% {
    transform: scale(1);
    filter: drop-shadow(0 0 12px rgba(212, 175, 55, 0.4));
  }
  90% {
    transform: scale(0.99);
    filter: drop-shadow(0 0 10px rgba(212, 175, 55, 0.35));
  }
`;

export const borderBreathe = keyframes`
  0%, 100% { 
    border-color: rgba(212, 175, 55, 0.1);
    box-shadow: 
      0 0 8px rgba(212, 175, 55, 0.05),
      0 0 15px rgba(212, 175, 55, 0.03),
      inset 0 0 8px rgba(212, 175, 55, 0.02);
  }
  10% {
    border-color: rgba(212, 175, 55, 0.15);
    box-shadow: 
      0 0 12px rgba(212, 175, 55, 0.08),
      0 0 20px rgba(212, 175, 55, 0.05),
      inset 0 0 10px rgba(212, 175, 55, 0.03);
  }
  20% {
    border-color: rgba(212, 175, 55, 0.2);
    box-shadow: 
      0 0 16px rgba(212, 175, 55, 0.12),
      0 0 25px rgba(212, 175, 55, 0.07),
      inset 0 0 12px rgba(212, 175, 55, 0.04);
  }
  30% {
    border-color: rgba(212, 175, 55, 0.25);
    box-shadow: 
      0 0 20px rgba(212, 175, 55, 0.16),
      0 0 30px rgba(212, 175, 55, 0.09),
      inset 0 0 15px rgba(212, 175, 55, 0.05);
  }
  40% {
    border-color: rgba(212, 175, 55, 0.3);
    box-shadow: 
      0 0 24px rgba(212, 175, 55, 0.2),
      0 0 35px rgba(212, 175, 55, 0.12),
      inset 0 0 18px rgba(212, 175, 55, 0.06);
  }
  50% { 
    border-color: rgba(212, 175, 55, 0.35);
    box-shadow: 
      0 0 28px rgba(212, 175, 55, 0.25),
      0 0 40px rgba(212, 175, 55, 0.15),
      inset 0 0 20px rgba(212, 175, 55, 0.08);
  }
  60% {
    border-color: rgba(212, 175, 55, 0.3);
    box-shadow: 
      0 0 24px rgba(212, 175, 55, 0.2),
      0 0 35px rgba(212, 175, 55, 0.12),
      inset 0 0 18px rgba(212, 175, 55, 0.06);
  }
  70% {
    border-color: rgba(212, 175, 55, 0.25);
    box-shadow: 
      0 0 20px rgba(212, 175, 55, 0.16),
      0 0 30px rgba(212, 175, 55, 0.09),
      inset 0 0 15px rgba(212, 175, 55, 0.05);
  }
  80% {
    border-color: rgba(212, 175, 55, 0.2);
    box-shadow: 
      0 0 16px rgba(212, 175, 55, 0.12),
      0 0 25px rgba(212, 175, 55, 0.07),
      inset 0 0 12px rgba(212, 175, 55, 0.04);
  }
  90% {
    border-color: rgba(212, 175, 55, 0.15);
    box-shadow: 
      0 0 12px rgba(212, 175, 55, 0.08),
      0 0 20px rgba(212, 175, 55, 0.05),
      inset 0 0 10px rgba(212, 175, 55, 0.03);
  }
`;

export const glowPulse = keyframes`
  0%, 100% { 
    opacity: 0.1;
    transform: translate(-50%, -50%) scale(0.9);
  }
  10% {
    opacity: 0.15;
    transform: translate(-50%, -50%) scale(0.92);
  }
  20% {
    opacity: 0.2;
    transform: translate(-50%, -50%) scale(0.94);
  }
  30% {
    opacity: 0.25;
    transform: translate(-50%, -50%) scale(0.96);
  }
  40% {
    opacity: 0.3;
    transform: translate(-50%, -50%) scale(0.98);
  }
  50% { 
    opacity: 0.4;
    transform: translate(-50%, -50%) scale(1);
  }
  60% {
    opacity: 0.3;
    transform: translate(-50%, -50%) scale(0.98);
  }
  70% {
    opacity: 0.25;
    transform: translate(-50%, -50%) scale(0.96);
  }
  80% {
    opacity: 0.2;
    transform: translate(-50%, -50%) scale(0.94);
  }
  90% {
    opacity: 0.15;
    transform: translate(-50%, -50%) scale(0.92);
  }
`;

export const skewFadeIn = keyframes`
  from { 
    opacity: 0; 
    transform: skewX(-15deg) translateX(-50px); 
  }
  to { 
    opacity: 1; 
    transform: skewX(-10deg) translateX(0); 
  }
`;

export const floatUp = keyframes`
  from { 
    opacity: 0; 
    transform: translateY(20px); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0); 
  }
`;

export const slideIn = keyframes`
  from { 
    opacity: 0; 
    transform: translateX(-20px); 
  }
  to { 
    opacity: 1; 
    transform: translateX(0); 
  }
`;

export const glowing = keyframes`
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
`;

export const GlobalStyle = createGlobalStyle`
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    font-family: 'Arial', sans-serif;
    background: #000;
    color: #ffffff;
    overflow-x: hidden;
    line-height: 1.6;
  }

  html, body, #root {
    height: 100%;
  }

  a {
    color: inherit;
    text-decoration: none;
  }

  button {
    font-family: inherit;
    cursor: pointer;
    border: none;
    outline: none;
  }

  input, textarea, select {
    font-family: inherit;
    outline: none;
  }

  ul, ol {
    list-style: none;
  }

  img {
    max-width: 100%;
    height: auto;
    display: block;
  }

  /* Scrollbar styles */
  ::-webkit-scrollbar {
    width: 8px;
  }

  ::-webkit-scrollbar-track {
    background: rgba(10, 17, 40, 0.3);
  }

  ::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #d4af37 0%, #f4e99b 100%);
    border-radius: 4px;
  }

  ::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #f4e99b 0%, #d4af37 100%);
  }
`;

// Color constants
export const colors = {
  primary: '#d4af37',
  primaryLight: '#f4e99b',
  primaryDark: '#b8941f',
  white: '#ffffff',
  black: '#000000',
  darkBlue: '#0a1128',
  mediumBlue: '#1e2749',
  lightBlue: '#2d3748',
  overlay: 'rgba(44, 24, 16, 0.4)',
  overlayMedium: 'rgba(26, 15, 8, 0.6)',
  overlayDark: 'rgba(13, 9, 5, 0.7)',
};

// Common gradient styles
export const gradients = {
  primary: 'linear-gradient(135deg, #d4af37 0%, #f4e99b 100%)',
  background: 'linear-gradient(135deg, #0a1128 0%, #1e2749 50%, #2d3748 100%)',
  landingOverlay: 'linear-gradient(135deg, rgba(44, 24, 16, 0.4) 0%, rgba(26, 15, 8, 0.6) 50%, rgba(13, 9, 5, 0.7) 100%)',
  heroSection: 'linear-gradient(135deg, rgba(10, 17, 40, 0.8) 0%, rgba(30, 39, 73, 0.6) 100%)',
  beliefSection: 'linear-gradient(135deg, #1e2749 0%, #2d3748 100%)',
};

// Responsive breakpoints
export const breakpoints = {
  mobile: '480px',
  tablet: '768px',
  desktop: '1024px',
  large: '1400px',
};

// Media query helpers
export const media = {
  mobile: `@media (max-width: ${breakpoints.mobile})`,
  tablet: `@media (max-width: ${breakpoints.tablet})`,
  desktop: `@media (max-width: ${breakpoints.desktop})`,
  large: `@media (min-width: ${breakpoints.large})`,
};

// Common button styles
export const buttonStyles = css`
  padding: 15px 40px;
  background: ${gradients.primary};
  color: ${colors.black};
  border: none;
  border-radius: 30px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 
    0 8px 25px rgba(212, 175, 55, 0.3),
    0 0 0 1px rgba(212, 175, 55, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  letter-spacing: 0.5px;

  &:hover {
    transform: translateY(-3px) scale(1.05);
    box-shadow: 
      0 15px 35px rgba(212, 175, 55, 0.4),
      0 0 0 2px rgba(212, 175, 55, 0.7),
      inset 0 1px 0 rgba(255, 255, 255, 0.4);
  }

  &:active {
    transform: translateY(-1px) scale(1.02);
  }
`;

// Common card styles
export const cardStyles = css`
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.15) 0%, rgba(212, 175, 55, 0.05) 100%);
  border: 2px solid rgba(212, 175, 55, 0.4);
  border-radius: 20px;
  padding: 30px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.4s ease;
  backdrop-filter: blur(15px);
  position: relative;
  overflow: hidden;

  &:hover {
    background: rgba(212, 175, 55, 0.1);
    border-color: rgba(212, 175, 55, 0.6);
    transform: translateY(-5px);
    box-shadow: 0 20px 40px rgba(212, 175, 55, 0.3);
  }
`;