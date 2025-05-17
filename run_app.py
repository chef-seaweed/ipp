# Run Streamlit App
!pip install streamlit -q
!npm install localtunnel

# Get your own ip address. Will serve as pwd for localtunnel server
!wget -q -O - ipv4.icanhazip.com 

#Localtunnel is a tool that allows you to expose a local server to the internet.
!streamlit run newapp.py & > logs.txt & npx localtunnel --port 8501