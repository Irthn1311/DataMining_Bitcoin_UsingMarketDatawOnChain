README - ĐỒ ÁN KHAI PHÁ DỮ LIỆU BITCOIN

1. THÔNG TIN ĐỀ TÀI
Tên đề tài:
Khai phá dữ liệu Bitcoin dựa trên dữ liệu thị trường, dữ liệu on-chain và sự kiện chính trị lớn trên thế giới.

Mục tiêu:
- Khai phá dữ liệu Bitcoin để rút ra các tri thức có giá trị từ dữ liệu thị trường, dữ liệu on-chain và dữ liệu sự kiện.
- Phân tích trạng thái thị trường Bitcoin.
- Tìm mối liên hệ giữa khối lượng giao dịch và biến động giá.
- Phân tích trạng thái hoạt động của mạng Bitcoin.
- Tìm quy luật giữa các chỉ số on-chain.
- Phân tích biến động Bitcoin quanh các sự kiện chính trị lớn.
- Xác định nhóm đặc trưng quan trọng trong việc dự đoán ngày Bitcoin tăng hoặc giảm.

2. CẤU TRÚC THƯ MỤC

DataMining_Bitcoin_UsingMarketDatawOnChain/
│
├── data/
│   ├── btc_ohlcv_daily.csv
│   ├── btc_onchain_daily.csv
│   ├── political_events.csv
│   └── btc_merged_event_daily.csv
│
├── scripts/
│
├── notebooks/
│   └── main_analysis.ipynb
│
├── docs/
│
├── requirements.txt
└── readme.md

Lưu ý:
Tên file/thư mục có thể thay đổi tùy theo quá trình thực hiện, nhưng các thành phần chính cần có gồm: dữ liệu, mã nguồn, notebook phân tích, báo cáo và file hướng dẫn.

3. MÔ TẢ CÁC FILE DỮ LIỆU

3.1. data/btc_ohlcv_daily.csv

Đây là Dataset 1 - dữ liệu thị trường Bitcoin theo ngày.

Nguồn dữ liệu:
- Yahoo Finance thông qua thư viện yfinance.

Giai đoạn:
- Từ 2015-01-01 đến ngày thu thập dữ liệu.

Các cột chính:
- date: ngày giao dịch.
- open: giá mở cửa.
- high: giá cao nhất trong ngày.
- low: giá thấp nhất trong ngày.
- close: giá đóng cửa.
- adj_close: giá đóng cửa điều chỉnh.
- volume: khối lượng giao dịch.

Mục đích sử dụng:
- Phân tích trạng thái thị trường Bitcoin.
- Tạo các đặc trưng như return, volatility, volume_change, high_low_range, ma_ratio.
- Phục vụ bài toán phân cụm và phân tích mối liên hệ giữa volume và biến động giá.

3.2. data/btc_onchain_daily.csv

Đây là Dataset 2 - dữ liệu on-chain của Bitcoin theo ngày.

Nguồn dữ liệu:
- Coin Metrics Community API.
- Blockchain.com Charts API.

Các cột chính:
- date: ngày.
- price_usd: giá Bitcoin theo USD từ Coin Metrics.
- active_addresses: số địa chỉ ví hoạt động.
- tx_count: số lượng giao dịch.
- hash_rate: sức mạnh tính toán của mạng.
- supply_current: nguồn cung Bitcoin hiện tại.
- fee_usd: tổng phí giao dịch USD, bổ sung từ Blockchain.com.
- difficulty: độ khó khai thác, bổ sung từ Blockchain.com.
- miner_revenue_usd: doanh thu miner USD, bổ sung từ Blockchain.com.
- estimated_transaction_volume_usd: khối lượng giao dịch ước tính bằng USD, bổ sung từ Blockchain.com.

Ghi chú:
Một số chỉ số như FeeTotUSD, DiffMean, RevUSD và TxTfrValAdjUSD trên Coin Metrics Community API bị giới hạn quyền truy cập. Vì vậy, nhóm bổ sung các chỉ số tương ứng hoặc gần tương đương từ Blockchain.com Charts API.

Mục đích sử dụng:
- Phân tích trạng thái hoạt động của mạng Bitcoin.
- Tìm quy luật giữa các chỉ số on-chain.
- Phục vụ phân cụm và phân tích kết hợp.

3.3. data/political_events.csv

Đây là Dataset sự kiện chính trị và sự kiện lớn có khả năng ảnh hưởng đến Bitcoin.

Các cột chính:
- date: ngày xảy ra sự kiện.
- event_name: tên sự kiện.
- event_type: loại sự kiện.
- region: khu vực.
- severity: mức độ quan trọng của sự kiện.

Ví dụ sự kiện:
- Brexit referendum.
- US presidential election.
- WHO declares COVID-19 a pandemic.
- Russia invades Ukraine.
- Israel-Hamas war begins.
- US spot Bitcoin ETF approval.
- Bitcoin halving.

Mục đích sử dụng:
- Phân tích Bitcoin có biến động bất thường trước và sau các sự kiện lớn hay không.
- Tạo các biến event_today, event_window_3d, event_window_7d, event_window_14d.

Ghi chú:
File này là dữ liệu sự kiện được xây dựng thủ công. Khi viết báo cáo, cần kiểm tra lại ngày sự kiện và bổ sung nguồn tham khảo nếu cần.

3.4. data/btc_merged_event_daily.csv

Đây là Dataset 3 - dữ liệu tổng hợp.

Nguồn dữ liệu:
- Dataset 1: btc_ohlcv_daily.csv.
- Dataset 2: btc_onchain_daily.csv.
- Dataset sự kiện: political_events.csv.

Cách tạo:
- Gộp dữ liệu theo cột date.
- Tạo thêm các đặc trưng kỹ thuật, on-chain change, event features và target classification.

Các nhóm cột chính:

Market features:
- return_1d
- return_7d
- abs_return_1d
- volatility_7
- volume_change
- high_low_range
- ma_7
- ma_30
- ma_ratio

On-chain features:
- active_addresses
- tx_count
- hash_rate
- supply_current
- fee_usd
- difficulty
- miner_revenue_usd
- estimated_transaction_volume_usd
- active_addresses_change
- tx_count_change
- hash_rate_change
- fee_usd_change
- difficulty_change
- miner_revenue_usd_change
- supply_current_change
- estimated_transaction_volume_usd_change

Event features:
- event_today
- event_window_3d
- event_window_7d
- event_window_14d
- event_name
- event_type
- region
- severity

Association flags:
- volume_change_high
- abs_return_1d_high
- volatility_7_high
- high_low_range_high
- active_addresses_change_high
- tx_count_change_high
- fee_usd_change_high
- miner_revenue_usd_change_high
- hash_rate_change_high
- difficulty_change_high
- estimated_transaction_volume_usd_change_high

Target:
- target_next_day_up:
  + 1: giá Bitcoin ngày tiếp theo tăng.
  + 0: giá Bitcoin ngày tiếp theo giảm hoặc không tăng.

4. MÔ TẢ FILE MÃ NGUỒN

4.1. scripts/fetchData.py

Chức năng:
- Tải dữ liệu OHLCV Bitcoin từ Yahoo Finance.
- Tải dữ liệu on-chain từ Coin Metrics Community API.
- Bổ sung một số chỉ số on-chain từ Blockchain.com Charts API.
- Tạo file political_events.csv.
- Tạo các đặc trưng mới cho dữ liệu OHLCV và on-chain.
- Tạo các biến event window.
- Gộp các dataset thành btc_merged_event_daily.csv.

Cách chạy:
Mở terminal tại thư mục gốc dự án và chạy:

python scripts/fetchData.py

Kết quả sau khi chạy:
- data/btc_ohlcv_daily.csv
- data/btc_onchain_daily.csv
- data/political_events.csv
- data/btc_merged_event_daily.csv

5. MÔI TRƯỜNG CÀI ĐẶT

Ngôn ngữ:
- Python 3.x

Các thư viện chính:
- pandas
- numpy
- requests
- yfinance

Cài đặt thư viện:
pip install -r requirements.txt

Nội dung file requirements.txt:
pandas>=2.0.0
numpy>=1.24.0
requests>=2.31.0
yfinance>=0.2.40

6. CÁC CÂU HỎI KHAI PHÁ DỮ LIỆU

6.1. Dataset 1 - Bitcoin OHLCV

Câu hỏi 1:
Bitcoin thường có những trạng thái thị trường nào dựa trên lợi suất, độ biến động và khối lượng giao dịch?

Loại bài toán:
- Clustering.

Thuật toán dự kiến:
- K-Means.
- DBSCAN.
- Hierarchical Clustering.

Tri thức cần rút ra:
- Các trạng thái thị trường như ổn định, tăng mạnh, giảm mạnh, biến động cao.
- Đặc điểm của từng trạng thái theo return, volatility, volume_change và high_low_range.

Câu hỏi 2:
Khi khối lượng giao dịch tăng đột biến, Bitcoin có thường biến động giá mạnh hơn không?

Loại bài toán:
- Association Analysis / Correlation Analysis.

Thuật toán dự kiến:
- Correlation Analysis.
- Apriori.
- FP-Growth.

Tri thức cần rút ra:
- Các luật như volume_high -> volatility_high hoặc volume_high -> abs_return_high.
- Mối liên hệ giữa volume và biến động giá.

6.2. Dataset 2 - Bitcoin On-chain Metrics

Câu hỏi 1:
Mạng Bitcoin thường có những trạng thái hoạt động nào dựa trên active addresses, tx_count, fees, hash rate và difficulty?

Loại bài toán:
- Clustering.

Thuật toán dự kiến:
- K-Means.
- DBSCAN.
- Hierarchical Clustering.

Tri thức cần rút ra:
- Các trạng thái mạng như bình thường, sôi động, phí cao/nghẽn mạng, thay đổi về mining/network.

Câu hỏi 2:
Khi mạng Bitcoin sôi động hoặc nghẽn, những chỉ số on-chain nào thường tăng cùng nhau?

Loại bài toán:
- Association Analysis.

Thuật toán dự kiến:
- Apriori.
- FP-Growth.
- Eclat nếu cần.

Tri thức cần rút ra:
- Các luật như active_addresses_high + tx_count_high -> fee_usd_high.
- fee_usd_high -> miner_revenue_usd_high.
- hash_rate_high -> difficulty_high.

6.3. Dataset 3 - OHLCV + On-chain + Event

Câu hỏi 1:
Các sự kiện chính trị lớn có đi kèm với thay đổi bất thường về return, volatility, volume và on-chain activity của Bitcoin không?

Loại bài toán:
- Time Series Event Study / Statistical Analysis.

Phương pháp dự kiến:
- Event Window Analysis.
- Before-after comparison.
- Statistical test như t-test hoặc Mann-Whitney U test.

Tri thức cần rút ra:
- Bitcoin có biến động mạnh hơn quanh các sự kiện lớn hay không.
- Volume và hoạt động on-chain có thay đổi bất thường trước/sau sự kiện hay không.

Câu hỏi 2:
Dựa vào yếu tố nào để xác định một ngày Bitcoin có xu hướng tăng hay giảm: market features, on-chain features hay event features?

Loại bài toán:
- Classification + Feature Importance.

Thuật toán dự kiến:
- Logistic Regression.
- Random Forest.
- XGBoost.

Tri thức cần rút ra:
- Nhóm đặc trưng nào quan trọng nhất trong dự đoán ngày tăng/giảm.
- Market features, on-chain features hay event features đóng góp nhiều hơn.

7. HƯỚNG MỞ RỘNG

Ngoài các câu hỏi khai phá dữ liệu chính, nhóm có thể triển khai thêm phần dự đoán xu hướng giá Bitcoin.

Mục tiêu:
- Kiểm tra xem các đặc trưng mới sinh ra từ quá trình khai phá dữ liệu có giúp cải thiện khả năng dự đoán ngày Bitcoin tăng/giảm hay không.

Cách làm:
- Baseline: dùng các feature gốc từ OHLCV và on-chain.
- Mở rộng: thêm market_cluster, network_cluster, association flags và event features.
- So sánh kết quả dự đoán trước và sau khi thêm feature khai phá.

Mô hình dự kiến:
- Logistic Regression.
- Random Forest.
- XGBoost.

Chỉ số đánh giá:
- Accuracy.
- Precision.
- Recall.
- F1-score.
- AUC.

8. QUY TRÌNH THỰC HIỆN

Bước 1:
Thu thập dữ liệu bằng scripts/fetchData.py.

Bước 2:
Kiểm tra dữ liệu:
- Số dòng, số cột.
- Kiểu dữ liệu.
- Missing values.
- Dữ liệu trùng.
- Dữ liệu ngoại lai.

Bước 3:
Tiền xử lý:
- Chuyển date về datetime.
- Sắp xếp theo thời gian.
- Xử lý missing values.
- Chuẩn hóa dữ liệu cho clustering.
- Rời rạc hóa dữ liệu cho association.
- Encode event features nếu dùng classification.

Bước 4:
Phân tích dữ liệu khám phá:
- Thống kê mô tả.
- Histogram.
- Boxplot.
- Line chart theo thời gian.
- Correlation heatmap.
- Phân tích đơn biến và đa biến.

Bước 5:
Khai phá dữ liệu theo 6 câu hỏi chính.

Bước 6:
Đánh giá mô hình:
- Classification: Accuracy, Precision, Recall, F1-score, AUC.
- Clustering: Silhouette Score, Davies-Bouldin Index.
- Association: Support, Confidence, Lift.
- Event Study: so sánh trước/sau, kiểm định thống kê.

Bước 7:
Trình bày kết quả và thảo luận:
- Tri thức rút ra.
- Ý nghĩa thực tế.
- Ưu điểm, nhược điểm.
- Hạn chế của dữ liệu và mô hình.
- Hướng phát triển.

9. LƯU Ý KHI CHẠY VÀ PHÂN TÍCH

- Dữ liệu được lấy theo ngày từ 2015-01-01 đến ngày chạy script.
- Một số dòng đầu sẽ bị thiếu do rolling window, ví dụ ma_30 cần 30 ngày đầu.
- Một số cột change sẽ thiếu dòng đầu tiên do pct_change.
- target_next_day_up sẽ thiếu dòng cuối vì không có dữ liệu ngày tiếp theo.
- Khi train/test cho dữ liệu chuỗi thời gian, không nên shuffle dữ liệu.
- Nên chia train/test theo thời gian, ví dụ 70% dữ liệu đầu làm train và 30% dữ liệu sau làm test.
- Không nên kết luận sự kiện chính trị là nguyên nhân trực tiếp gây biến động Bitcoin; chỉ nên kết luận là có hoặc không có dấu hiệu biến động bất thường quanh sự kiện.

10. GHI CHÚ VỀ NGUỒN DỮ LIỆU

- Dữ liệu OHLCV được lấy từ Yahoo Finance thông qua yfinance.
- Dữ liệu on-chain chính được lấy từ Coin Metrics Community API.
- Các chỉ số fee_usd, difficulty, miner_revenue_usd và estimated_transaction_volume_usd được bổ sung từ Blockchain.com Charts API do một số metric của Coin Metrics bị giới hạn quyền truy cập.
- Dữ liệu political_events.csv được xây dựng thủ công và cần bổ sung nguồn tham khảo trong báo cáo chính thức.
