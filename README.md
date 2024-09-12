# How to use

## 制御周期出力
```
candump -s 0 -d -L can0,7F0:7FF | python3 src/can_analysis/can_frequency.py
```

## CANメッセージ送受信エラー確認
```
candump -s 0 -d -L can0 | python3 src/can_analysis/can_message_comparison.py 
```