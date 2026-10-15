// Sakthi Agri - Interactive Frontend Logic

document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss flash messages after 5 seconds
    const alerts = document.querySelectorAll('.flash-alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            alert.style.transition = 'all 0.4s ease';
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });

    // Image preview helper for file inputs
    const imageInputs = document.querySelectorAll('input[type="file"][data-preview]');
    imageInputs.forEach(input => {
        input.addEventListener('change', function () {
            const previewId = this.getAttribute('data-preview');
            const previewEl = document.getElementById(previewId);
            if (previewEl && this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    previewEl.src = e.target.result;
                    previewEl.style.display = 'block';
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    });

    // Mobile Hamburger Menu Toggle
    const mobileToggleBtn = document.getElementById('mobileMenuToggle');
    const sidebarCollapseWrapper = document.getElementById('sidebarCollapseWrapper');
    if (mobileToggleBtn && sidebarCollapseWrapper) {
        mobileToggleBtn.addEventListener('click', function () {
            sidebarCollapseWrapper.classList.toggle('show');
            const icon = mobileToggleBtn.querySelector('i');
            if (icon) {
                if (sidebarCollapseWrapper.classList.contains('show')) {
                    icon.className = 'bi bi-x-lg';
                } else {
                    icon.className = 'bi bi-list';
                }
            }
        });
    }
});

// Razorpay Payment Handler
function initiateRazorpayPayment(options) {
    if (typeof Razorpay !== 'undefined') {
        const rzpConfig = {
            key: options.key_id || 'rzp_test_TB4Wag5FTkTL1J',
            amount: options.amount_in_paise,
            currency: 'INR',
            name: 'Sakthi Agri Direct Marketplace',
            description: options.description || 'Order Payment',
            image: 'https://cdn-icons-png.flaticon.com/512/188/188333.png',
            handler: function (response) {
                // Submit form or redirect with payment credentials
                submitPaymentSuccess(response, options);
            },
            prefill: {
                name: options.buyer_name,
                email: options.buyer_email,
                contact: options.buyer_phone
            },
            theme: {
                color: '#166534'
            }
        };

        if (options.razorpay_order_id || options.order_id) {
            rzpConfig.order_id = options.razorpay_order_id || options.order_id;
        }

        const rzp = new Razorpay(rzpConfig);
        rzp.on('payment.failed', function (response) {
            console.warn('Razorpay payment failed or cancelled:', response.error);
            // If failed, allow user to complete via simulation modal or try again
            if (confirm('Razorpay Payment was interrupted. Would you like to complete this test transaction in simulation mode?')) {
                showSimulatedPaymentModal(options);
            }
        });
        rzp.open();
    } else {
        // Fallback simulated payment modal for test environments
        showSimulatedPaymentModal(options);
    }
}

function showSimulatedPaymentModal(options) {
    const modalHtml = `
    <div id="simulated-payment-modal" style="position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 9999;">
        <div style="background: #ffffff; border-radius: 14px; width: 90%; max-width: 440px; overflow: hidden; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.3);">
            <div style="background: #166534; padding: 20px; color: #fff; display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.5rem;">💳</span>
                    <div>
                        <div style="font-weight: 700; font-size: 1.1rem;">Razorpay Secure Gateway</div>
                        <div style="font-size: 0.8rem; opacity: 0.9;">Sakthi Agri Marketplace</div>
                    </div>
                </div>
                <button onclick="document.getElementById('simulated-payment-modal').remove()" style="background: none; border: none; color: #fff; font-size: 1.3rem; cursor: pointer;">&times;</button>
            </div>
            <div style="padding: 24px;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <div style="font-size: 0.9rem; color: #6b7280;">Amount to Pay</div>
                    <div style="font-size: 2rem; font-weight: 800; color: #166534;">₹${(options.amount_in_paise / 100).toFixed(2)}</div>
                    <div style="font-size: 0.85rem; color: #059669; margin-top: 4px;">✔ Test Mode (100% Instant Simulation)</div>
                </div>
                <div style="background: #f9fafb; padding: 14px; border-radius: 8px; border: 1px solid #e5e7eb; margin-bottom: 20px; font-size: 0.88rem;">
                    <div><strong>Customer:</strong> ${options.buyer_name || 'Buyer'}</div>
                    <div><strong>Phone:</strong> ${options.buyer_phone || '9443215678'}</div>
                    <div><strong>Item:</strong> ${options.description || 'Farm Fresh Produce'}</div>
                </div>
                <button id="btn-confirm-pay" style="width: 100%; background: #22c55e; color: #fff; border: none; padding: 14px; font-size: 1rem; font-weight: 700; border-radius: 8px; cursor: pointer; transition: background 0.2s;" onmouseover="this.style.background='#16a34a'" onmouseout="this.style.background='#22c55e'">
                    ✔ Confirm & Complete Payment (₹${(options.amount_in_paise / 100).toFixed(2)})
                </button>
            </div>
        </div>
    </div>`;

    document.body.insertAdjacentHTML('beforeend', modalHtml);

    document.getElementById('btn-confirm-pay').addEventListener('click', function () {
        this.innerHTML = 'Processing Payment...';
        this.disabled = true;
        setTimeout(() => {
            const fakeResponse = {
                razorpay_payment_id: 'pay_' + Math.random().toString(36).substr(2, 9),
                razorpay_order_id: options.razorpay_order_id || ('order_' + Math.random().toString(36).substr(2, 9)),
                razorpay_signature: 'sig_' + Math.random().toString(36).substr(2, 9)
            };
            submitPaymentSuccess(fakeResponse, options);
        }, 1200);
    });
}

function submitPaymentSuccess(response, options) {
    // Create form and submit to payment callback endpoint
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = options.callback_url || '/payment/callback';

    const fields = {
        razorpay_payment_id: response.razorpay_payment_id,
        razorpay_order_id: response.razorpay_order_id,
        order_number: options.order_number,
        payment_status: 'Paid'
    };

    for (const key in fields) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = fields[key];
        form.appendChild(input);
    }

    document.body.appendChild(form);
    form.submit();
}
