# Memory Bank - IoT Air Quality Prediction System

## Giới thiệu
Memory Bank là hệ thống lưu trữ kiến thức của dự án, giúp duy trì context giữa các phiên làm việc với AI assistant.

## Cấu trúc Files

| File | Mục đích |
|------|----------|
| `projectbrief.md` | Tổng quan dự án, yêu cầu, phạm vi |
| `productContext.md` | Vấn đề cần giải quyết, personas, goals |
| `systemPatterns.md` | Kiến trúc hệ thống, design patterns |
| `techContext.md` | Stack công nghệ, cấu hình, features |
| `activeContext.md` | Trạng thái hiện tại, next steps |
| `progress.md` | Tiến độ, issues, milestones |

## Cách sử dụng

### Bắt đầu phiên làm việc mới
AI assistant sẽ tự động đọc tất cả files trong memory-bank để hiểu context.

### Cập nhật Memory Bank
Khi có thay đổi quan trọng, nói "update memory bank" để cập nhật.

### Quick Reference

**Model Performance:**
- CO(GT): R²=0.836, MAE=0.361
- C6H6(GT): R²=0.818, MAE=1.664

**27 Features:**
- 4 cyclical (hour_sin/cos, day_sin/cos)
- 4 lag (1hr, 24hr for CO and C6H6)
- 8 rolling (mean/std/max over 3hr and 24hr)
- 4 diff (momentum features)
- 4 interaction (diff × cyclical)
- 3 state (daytime, morning_rush, evening_rush)

**Key Commands:**
```bash
# Start server
python server.py

# Run pipeline
python datapipe.py

# Train model
python main.py
```

---

*Last updated: 2025-12-30*
