# **Mô phỏng Mô hình Rủi ro Cramer-Lundberg bằng Quá trình Poisson**

## **Giới thiệu**

Dự án này cung cấp một hệ thống trực quan hóa và tính toán Mô hình rủi ro Cramer-Lundberg, phục vụ cho việc đánh giá xác suất phá sản (Ruin Probability) trong Lý thuyết rủi ro (Risk Theory). Ứng dụng hoạt động trên môi trường cục bộ, sử dụng kiến trúc dựa trên Quá trình Poisson phức hợp (Compound Poisson Process) để mô phỏng quỹ đạo tài sản và đánh giá tính an toàn của hệ thống theo thời gian thực.

## **Kiến trúc hệ thống**

1. **Khởi tạo tham số (Input Parameters):** Thu thập các biến số đầu vào bao gồm vốn ban đầu $u$, tốc độ thu phí $c$, cường độ yêu cầu bồi thường $\\lambda$, và mức bồi thường trung bình $\\mu$.  
2. **Động cơ ngẫu nhiên (Stochastic Engine):** Lõi toán học sử dụng thuật toán nghịch đảo (Inverse Transform Sampling) để sinh các khoảng thời gian chờ tuân theo phân phối Mũ, hình thành Quá trình Poisson $N(t)$.  
3. **Quá trình phức hợp (Compound Process):** Sinh giá trị tổn thất ngẫu nhiên $X\_i$ cho mỗi sự kiện, tính toán quỹ đạo tài sản thông qua phương trình $U(t) \= u \+ ct \- \\sum\_{i=1}^{N(t)} X\_i$.  
4. **Giao diện người dùng (UI):** Triển khai cục bộ thông qua Streamlit nhằm cung cấp bảng điều khiển tương tác các tham số.  
5. **Trực quan hóa (Visualization):** Sử dụng Matplotlib kết hợp thiết kế đồ thị hàm bậc thang (step function) để minh họa quỹ đạo và xác định thời điểm phá sản ($U(t) \< 0$).

## **Yêu cầu môi trường**

* Python 3.10 trở lên.  
* Môi trường Python được cài đặt các gói phụ thuộc phục vụ tính toán ma trận và render UI.

### **Danh sách các thư viện (requirements.txt)**


```plaintext
numpy  
pandas  
matplotlib  
scipy  
streamlit
```
## **Cài đặt và triển khai**

1. **Thiết lập môi trường ảo và cài đặt thư viện:**


```
python \-m venv venv  
\# Trên Linux/macOS  
source venv/bin/activate    
\# Trên Windows  
venv\\Scripts\\activate

pip install \-r requirements.txt
```
2. **Khởi chạy ứng dụng UI:**  
   Đảm bảo bạn đang ở thư mục gốc của dự án, thực thi lệnh sau để khởi chạy máy chủ cục bộ:


```
streamlit run app.py
```
3. **Thực thi luồng mô phỏng:**  
* Điều chỉnh các thanh trượt trên UI cho các biến số $\\lambda, \\mu, u, c$.  
* Ứng dụng sẽ tự động sinh quỹ đạo mẫu mới và kiểm tra điều kiện sinh lời an toàn (Net Profit Condition: $c \> \\lambda \\mu$) ngay lập tức.

## **Hướng phát triển và tối ưu**

* **Quá trình Poisson không đồng nhất (NHPP):** Mở rộng mô hình cốt lõi để tham số $\\lambda$ có khả năng biến thiên theo thời gian $\\lambda(t)$, phản ánh tính chu kỳ của dữ liệu thực tiễn.  
* **Đa dạng hóa phân phối rủi ro:** Xây dựng các luồng sinh số ngẫu nhiên cho các phân phối đuôi dày (Heavy-tailed distributions) như Pareto hoặc Log-Normal để mô phỏng các mức bồi thường mang tính thảm họa (Black Swan events).

## **Tài liệu tham khảo**

1. Ross, S. M. (2014). *Introduction to Probability Models* (11th ed.). Academic Press.  
2. Klugman, S. A., Panjer, H. H., & Willmot, G. E. (2012). *Loss Models: From Data to Decisions* (4th ed.). John Wiley & Sons.  
3. Asmussen, S., & Albrecher, H. (2010). *Ruin Probabilities* (2nd ed.). World Scientific.
