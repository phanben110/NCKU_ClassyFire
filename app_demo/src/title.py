import streamlit as st
def title_app(input_text):
    st.markdown(f"""
        <style>
            .header-container {{
                background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
                padding: 16px 35px;
                border-radius: 12px;
                box-shadow: 0 4px 25px rgba(238, 90, 82, 0.15);
                text-align: center;
                margin: 25px auto;
                position: relative;
                overflow: hidden;
                width: 100%;
                backdrop-filter: blur(10px);
            }}
            
            .header-container::before {{
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(255, 255, 255, 0.08) 0%, transparent 70%);
                animation: shimmer 4s ease-in-out infinite;
            }}
            
            .header-text {{
                font-size: 42px;
                font-weight: 700;
                background: linear-gradient(45deg, #ffffff 0%, #f8f9fa 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                font-family: 'Inter', 'SF Pro Display', 'Segoe UI', sans-serif;
                margin: 0;
                letter-spacing: -1.2px;
                text-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                position: relative;
                z-index: 1;
                display: inline-block;
                line-height: 1.1;
            }}
            
            @keyframes shimmer {{
                20%, 100% {{ 
                    opacity: 0.2;
                    transform: rotate(0deg);
                }}
                50% {{ 
                    opacity: 0.6;
                    transform: rotate(180deg);
                }}
            }}
            
            @media (max-width: 768px) {{
                .header-container {{
                    width: 85%;
                    padding: 14px 25px;
                }}
                .header-text {{
                    font-size: 26px;
                    letter-spacing: -0.8px;
                }}
            }}
            
            @media (max-width: 480px) {{
                .header-container {{
                    width: 95%;
                    padding: 12px 20px;
                }}
                .header-text {{
                    font-size: 22px;
                    letter-spacing: -0.6px;
                }}
            }}
            
            .header-container:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 35px rgba(238, 90, 82, 0.25);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }}
            
            .header-container:hover .header-text {{
                transform: scale(1.02);
                transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }}
        </style>
        <div class="header-container">
            <span class="header-text">{input_text}</span>
        </div>
    """, unsafe_allow_html=True)
