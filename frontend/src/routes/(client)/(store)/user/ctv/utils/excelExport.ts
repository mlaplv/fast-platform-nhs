export function exportLedgerToExcel(items: any[], fileName: string, ctvCode: string, siteName: string = "Osmo") {
  const BOM = '\uFEFF';
  let html = `
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        table { border-collapse: collapse; font-family: sans-serif; }
        th { background-color: #c9933b; color: white; font-weight: bold; border: 1px solid #ddd; padding: 8px; text-transform: uppercase; font-size: 11px; }
        td { border: 1px solid #ddd; padding: 8px; font-size: 11px; vertical-align: top; }
        .title-row { font-size: 16px; font-weight: bold; text-align: center; color: #333; }
        .header-meta { font-size: 10px; color: #666; font-style: italic; }
        .allocated-box { background-color: #fcf8e3; border: 1px solid #faebcc; padding: 6px; border-radius: 4px; font-size: 9px; }
        .allocated-item { border-bottom: 1px dashed #e4e4e4; padding-bottom: 4px; margin-bottom: 4px; }
        .allocated-item:last-child { border-bottom: none; }
        .status-paid { color: #2e7d32; font-weight: bold; }
        .status-confirmed { color: #f57c00; font-weight: bold; }
        .status-pending { color: #1976d2; font-weight: bold; }
        .number-cell { text-align: right; }
      </style>
    </head>
    <body>
      <table>
        <tr>
          <td colspan="11" class="title-row">${fileName.toUpperCase()}</td>
        </tr>
        <tr>
          <td colspan="11" class="header-meta">Ngày xuất báo cáo: ${new Date().toLocaleString('vi-VN')} | ${siteName} Elite Financial Protection</td>
        </tr>
        <tr><td colspan="11"></td></tr>
        <tr>
          <th>Mã Đơn hàng</th>
          <th>Ngày giao dịch</th>
          <th>Mã CTV</th>
          <th>Trạng thái</th>
          <th>Doanh thu gộp</th>
          <th>Khấu trừ ship</th>
          <th>Thuế thu nhập</th>
          <th>Doanh thu thuần</th>
          <th>Tỷ lệ chiết khấu tb</th>
          <th>Hoa hồng thực nhận</th>
          <th>Chi tiết phân bổ (Sản phẩm / Quà tặng)</th>
        </tr>
  `;

  items.forEach(item => {
    let bd: any = null;
    try {
      if (item.admin_note) {
        bd = JSON.parse(item.admin_note);
      }
    } catch (e) {}

    const orderTotal = bd ? bd.order_total : item.order_amount;
    const shippingFee = bd ? bd.shipping_fee : 0;
    const taxDeduction = bd ? bd.tax_deduction : 0;
    const revenueNet = bd ? bd.revenue_net : (orderTotal - shippingFee);
    const rateApplied = bd ? bd.rate_applied : (item.rate_applied || 0.05);
    const commAmount = item.commission_amount;
    
    let statusText = 'Chờ duyệt';
    let statusClass = 'status-pending';
    if (item.status === 'CONFIRMED') {
      statusText = 'Khả dụng';
      statusClass = 'status-confirmed';
    } else if (item.status === 'PAID') {
      statusText = 'Đã chi trả';
      statusClass = 'status-paid';
    } else if (item.status === 'CANCELLED' || item.status === 'VOIDED') {
      statusText = 'Đã hủy';
      statusClass = '';
    }

    let allocationText = '';
    if (bd && bd.is_allocated && bd.allocation_details && bd.allocation_details.length > 0) {
      bd.allocation_details.forEach((detail: any) => {
        allocationText += `• ${detail.name} (x${detail.qty}): pb ${detail.fraction}% (${detail.allocated_revenue.toLocaleString('vi-VN')}đ) | chiết khấu ${(detail.rate * 100).toFixed(1)}% | hoa hồng: +${detail.gross_commission.toLocaleString('vi-VN')}đ\n`;
      });
    } else {
      allocationText = 'Không có thông tin phân bổ lẻ';
    }

    html += `
      <tr>
        <td>#${item.order_id.split('-')[0].toUpperCase()}</td>
        <td>${new Date(item.created_at || item.requested_at).toLocaleDateString('vi-VN')}</td>
        <td>${item.ctv_code || ctvCode}</td>
        <td class="${statusClass}">${statusText}</td>
        <td class="number-cell">${orderTotal.toLocaleString('vi-VN')}đ</td>
        <td class="number-cell">${shippingFee.toLocaleString('vi-VN')}đ</td>
        <td class="number-cell">${taxDeduction.toLocaleString('vi-VN')}đ</td>
        <td class="number-cell">${revenueNet.toLocaleString('vi-VN')}đ</td>
        <td class="number-cell">${(rateApplied * 100).toFixed(1)}%</td>
        <td class="number-cell" style="font-weight: bold; color: #c9933b;">+${commAmount.toLocaleString('vi-VN')}đ</td>
        <td style="white-space: pre-line;">${allocationText}</td>
      </tr>
    `;
  });

  html += `
      </table>
    </body>
    </html>
  `;

  const blob = new Blob([BOM + html], { type: 'application/vnd.ms-excel;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${fileName}_${new Date().toISOString().slice(0, 10)}.xls`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
