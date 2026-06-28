// Smart CRM 品牌与 Ant Design 主题令牌
export const BRAND = {
  name: '智销 CRM',
  nameEn: 'Smart CRM',
  tagline: 'AI 销售增长助手',
  primary: '#2B54E6',
  primaryHover: '#1E40C8',
  primarySoft: '#EAF0FF',
}

export const antdTheme = {
  token: {
    colorPrimary: BRAND.primary,
    colorInfo: BRAND.primary,
    colorLink: BRAND.primary,
    borderRadius: 8,
    fontSize: 14,
    fontFamily:
      '"PingFang SC", "Microsoft YaHei", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    colorBgLayout: '#F4F6FB',
  },
  components: {
    Layout: {
      siderBg: '#FFFFFF',
      headerBg: '#FFFFFF',
      headerHeight: 56,
      bodyBg: '#F4F6FB',
    },
    Menu: {
      itemSelectedBg: BRAND.primarySoft,
      itemSelectedColor: BRAND.primary,
      itemBorderRadius: 8,
      itemMarginInline: 8,
      itemHeight: 42,
    },
    Card: {
      borderRadiusLG: 12,
    },
    Table: {
      headerBg: '#F7F9FC',
      headerColor: '#5B6B86',
      rowHoverBg: '#F5F8FF',
    },
  },
}
