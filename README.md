# **Cramer-Lundberg Poisson Simulator**

## **Mục tiêu**

Dự án này mô phỏng Mô hình rủi ro Cramer-Lundberg bằng Quá trình Poisson phức hợp, với thuật toán sinh biến ngẫu nhiên minh bạch theo phương pháp nghịch đảo (Inverse Transform Sampling). Chương trình in vết (trace log) 10 biến cố đầu tiên và trực quan hóa quỹ đạo tài sản bằng biểu đồ hàm bậc thang, kèm đường biên phá sản $y=0$.

## **Mô hình toán học**

$$ U(t) = u + c t - \sum_{i=1}^{N(t)} Y_i $$

* $N(t)$ là quá trình Poisson với cường độ $\lambda$.
* Khoảng chờ $W_i \sim \text{Exp}(\lambda)$, sinh bằng $W_i = -\frac{1}{\lambda}\ln(U)$.
* Mức bồi thường $Y_i \sim \text{Exp}(1/\mu)$, sinh bằng $Y_i = -\mu \ln(U)$.
* Phá sản khi $U(T_n) < 0$.

## **Cấu trúc mã nguồn**

* `cl_model.py`: Lớp `CramerLundbergModel` và lõi mô phỏng.
* `main.py`: Chương trình chạy mẫu từ dòng lệnh.

## **Cài đặt**

```
python -m venv venv
# Trên Windows
venv\Scripts\activate

pip install -r requirements.txt
```

## **Cách chạy**

```
python main.py
```

Ví dụ tuỳ chỉnh tham số:

```
python main.py --u 10000 --c 600 --lambda-rate 1.2 --mu-claim 200 --T 40
```

## **Trace log**

Bảng vết hiển thị 10 biến cố đầu tiên bao gồm: chỉ số sự kiện, thời gian chờ $W_i$, thời điểm $T_i$, mức bồi thường $Y_i$, dòng tiền thu vào $cT_i$, và số dư quỹ $U(T_i)$.

## **Ghi chú trực quan hóa**

Biểu đồ sử dụng hàm bậc thang để thể hiện chuỗi nhảy của quá trình hợp thành. Đường đỏ $y=0$ biểu thị ranh giới phá sản.

## **Tài liệu tham khảo**

1. Ross, S. M. (2014). *Introduction to Probability Models* (11th ed.). Academic Press.  
2. Klugman, S. A., Panjer, H. H., & Willmot, G. E. (2012). *Loss Models: From Data to Decisions* (4th ed.). John Wiley & Sons.  
3. Asmussen, S., & Albrecher, H. (2010). *Ruin Probabilities* (2nd ed.). World Scientific.
