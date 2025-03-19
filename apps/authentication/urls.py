from django.urls  import path
from .views import(
    GenerateQRCodeView,
    OTPLoginResetView,
    VerifyOTPView,
    Set2FAView,
    DisableOTPView,
    OTPLoginResetView,
    OTPLoginView
)

urlpatterns = [
    path("generate_qr_code/", GenerateQRCodeView.as_view(), name="generate-qr-code-view"),
    path("verify_otp/", VerifyOTPView.as_view(), name="verify-otp-view"), 
    path("set_2fa/", Set2FAView.as_view(), name="set-2fa-view"),
    path("disable_otp/", DisableOTPView.as_view(), name="disable-otp-view"),
    path("otp_login_reset/", OTPLoginResetView.as_view(), name="reset-otp-view"),
    path("opt_login/", OTPLoginView.as_view(), name="opt-login-view"),
]   