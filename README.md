
# NCKU_SMILE_Project

## 1. Download and Install Java
Download Java from the following link:  
[Java Download](https://www.java.com/en/download/manual.jsp)

Extract the downloaded file:
```bash
cd /usr/java
tar zxvf jre-8u421-linux-x64.tar.gz
```

## 2. Install R
Update your package list and install necessary tools:
```bash
sudo apt update
sudo apt install --no-install-recommends software-properties-common dirmngr
```

Add the CRAN repository for R:
```bash
sudo add-apt-repository "deb https://cloud.r-project.org/bin/linux/ubuntu $(lsb_release -cs)-cran40/"
wget -qO- https://cloud.r-project.org/bin/linux/ubuntu/marutter_pubkey.asc | sudo tee -a /etc/apt/trusted.gpg.d/cran_ubuntu_key.asc
```

Update the package list again and install R:
```bash
sudo apt update
sudo apt install r-base
```

Verify the R installation:
```bash
R --version
```

## 3. Install rJava
Update your package list and install the OpenJDK:
```bash
sudo apt update
sudo apt install openjdk-8-jdk
```

Check the Java version:
```bash
java -version
```

Configure R to use Java:
```bash
sudo R CMD javareconf
```

## 4. Install Required R Libraries
Open R and install the following packages:
```R
install.packages("webchem")
install.packages("fingerprint")
install.packages("rJava")
install.packages("rcdklibs")
install.packages("rcdk")
```

## 5. Install Necessary Python Libraries
Install the required Python libraries (modify based on your needs):
```bash
pip install pyper pandas
```
## 6. Start App 
```
bash runapp.sh 

```
or 
```
streamlit run app.py --server.port 1999
```
# NCKU_ClassyFire
