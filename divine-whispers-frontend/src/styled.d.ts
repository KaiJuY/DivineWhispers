import 'styled-components';

declare module 'styled-components' {
  export interface DefaultTheme {
    colors: {
      primary: string;
      primaryLight: string;
      primaryDark: string;
      white: string;
      black: string;
      darkBlue: string;
      mediumBlue: string;
      lightBlue: string;
    };
    gradients: {
      primary: string;
      background: string;
    };
    breakpoints: {
      mobile: string;
      tablet: string;
      desktop: string;
      large: string;
    };
  }
}