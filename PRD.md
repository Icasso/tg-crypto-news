# Product Requirements Document (PRD)
## Telegram Crypto News Bot

### **Project Overview**
A production-ready Telegram bot that delivers daily AAVE DeFi market updates to users. The bot provides real-time supply/borrow APY rates, market utilization data, and direct links to AAVE markets for detailed analysis.

### **Core Features**

#### **1. Daily Message Delivery**
- **Automated Scheduling**: Sends daily messages at 8:00 AM UTC via GitHub Actions
- **Manual Triggering**: Supports on-demand message generation for testing
- **Reliable Delivery**: Implements retry logic with exponential backoff
- **Error Handling**: Comprehensive error handling with specific exit codes

#### **2. AAVE Market Data Integration**
- **Real-time Market Data**: Fetches live APY rates from AAVE Base network
- **Multi-token Support**: Displays data for ETH, USDC, cbBTC, and DAI
- **Market Metrics**: Shows supply APY, borrow APY, utilization rates, and liquidity
- **Direct Market Access**: Provides clickable links to AAVE Base markets

#### **3. Message Formatting**
- **Card-style Layout**: Clean, readable format optimized for Telegram
- **Rich Text Support**: Uses Telegram markdown for enhanced readability
- **Timestamp Information**: Includes update time for data freshness
- **Professional Presentation**: Consistent emoji usage and structured layout

### **Technical Requirements**

#### **Architecture**
- **Modular Design**: Separation of concerns with dedicated modules
- **Async/Await**: Full asynchronous operation for performance
- **Type Safety**: Complete type hints throughout codebase
- **Error Handling**: Custom exception hierarchy with specific error types
- **Caching**: In-memory caching with 5-minute TTL for API optimization

#### **AAVE Integration**
- **Web3 Direct Calls**: Uses Web3.py for direct blockchain interaction
- **Base Network Focus**: Optimized for AAVE V3 on Base network
- **Rate Calculations**: Converts AAVE ray format to percentage APY
- **Health Monitoring**: Implements health checks for network connectivity
- **Retry Logic**: Exponential backoff for failed requests

#### **Configuration Management**
- **YAML Configuration**: Human-readable configuration files
- **Environment Variables**: Secure secret management
- **Validation**: Configuration validation at startup
- **Flexible Settings**: Easy customization of tokens and features

#### **Security & Deployment**
- **Secrets Management**: GitHub Secrets for sensitive data
- **Minimal Permissions**: Least privilege access patterns
- **Production Logging**: Structured logging with appropriate levels
- **CI/CD Pipeline**: Automated testing and deployment

### **Message Structure**
```
🏦 **AAVE Base Market**

💰 **ETH**
├ 📈 Supply: `1.78%`
├ 📉 Borrow: `2.50%`
├ 📊 Utilization: `83.5%`
└ 💧 Liquidity: `15,077`

💰 **USDC**
├ 📈 Supply: `3.89%`
├ 📉 Borrow: `4.12%`
├ 📊 Utilization: `94.3%`
└ 💧 Liquidity: `1,234,567`

🔗 **View Full Markets**
👉 [AAVE Base Markets](https://app.aave.com/?marketName=proto_base_v3)

⏰ Updated: 18:18 UTC
```

### **Supported Networks & Tokens**

#### **Primary Network**
- **Base Network**: AAVE V3 deployment on Base (Chain ID: 8453)

#### **Supported Tokens**
- **ETH** (WETH): 0x4200000000000000000000000000000000000006
- **USDC**: 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
- **cbBTC**: 0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf
- **DAI**: 0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb

### **Performance Requirements**
- **Response Time**: < 30 seconds for complete message generation
- **Availability**: 99.5% uptime for scheduled messages
- **Error Rate**: < 1% failure rate for message delivery
- **Cache Performance**: 95%+ cache hit rate for repeated requests

### **Monitoring & Alerting**
- **Health Checks**: Pre-flight network connectivity validation
- **Error Tracking**: Comprehensive error logging and categorization
- **Performance Metrics**: Request timing and success rate monitoring
- **GitHub Actions**: Workflow status and failure notifications

### **Future Enhancements**
- **Multi-network Support**: Extend to Ethereum, Polygon, Arbitrum
- **Additional Protocols**: Compound, Uniswap V3, Curve integration
- **User Customization**: Per-user token preferences and notification timing
- **Advanced Analytics**: Historical rate tracking and trend analysis
- **Interactive Commands**: Slash commands for on-demand data requests