/**
 * WebRTC video streaming utility - محسن للأجهزة المحمولة
 */
class WebRTCHandler {
    constructor() {
        this.peerConnection = null;
        this.videoElement = document.getElementById('webrtc-video');
        this.loadingIndicator = document.getElementById('loading-indicator');
        this.errorMessage = document.getElementById('error-message');
        this.noExercise = document.getElementById('no-exercise');
        this.localStream = null;
        this.currentExercise = null;
        this.currentCameraId = null; // تخزين معرف الكاميرا الحالية
        
        // معرفة نوع الجهاز
        this.isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        
        // إعدادات WebRTC مع خوادم STUN عامة
        this.config = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' },
                { urls: 'stun:stun2.l.google.com:19302' }
            ]
        };
        
        console.log('WebRTCHandler تم التهيئة بنجاح، جهاز محمول:', this.isMobile);
    }
    
    /**
     * تهيئة اتصال WebRTC لتمرين
     * @param {string} exerciseId - معرف التمرين للبث
     */
    async initConnection(exerciseId) {
        console.log('WebRTC: بدء الاتصال لتمرين', exerciseId);
        
        // إعادة ضبط أي اتصال موجود
        this.resetConnection();
        
        this.currentExercise = exerciseId;
        this.showLoading();
        
        try {
            // محاولة استخدام الطريقة التقليدية أولاً كخطة بديلة
            if (!this.isMobile) {
                try {
                    console.log('WebRTC: محاولة استخدام الطريقة التقليدية');
                    this.showLegacyStream(exerciseId);
                    console.log('WebRTC: نجح استخدام الطريقة التقليدية');
                    return; // الخروج إذا نجحت الطريقة التقليدية
                } catch (legacyError) {
                    console.warn("الطريقة التقليدية غير متاحة، جاري تجربة WebRTC", legacyError);
                }
            }
            
            // الحصول على تدفق الكاميرا
            try {
                console.log('محاولة الوصول إلى الكاميرا...');
                
                // إعدادات الكاميرا للأجهزة المحمولة
                const constraints = {
                    video: this.isMobile ? {
                        facingMode: { ideal: 'environment' }, // استخدام الكاميرا الخلفية بشكل افتراضي على الأجهزة المحمولة
                        width: { ideal: 640 },
                        height: { ideal: 480 }
                    } : {
                        width: { ideal: 640 },
                        height: { ideal: 480 }
                    },
                    audio: false
                };
                
                this.localStream = await navigator.mediaDevices.getUserMedia(constraints);
                
                // حفظ معرف الكاميرا الحالية
                const tracks = this.localStream.getVideoTracks();
                if (tracks.length > 0) {
                    const settings = tracks[0].getSettings();
                    this.currentCameraId = settings.deviceId;
                    console.log('تم استخدام الكاميرا:', settings.facingMode || 'غير محدد');
                }
                
                // عرض تدفق الكاميرا المحلي على الصفحة
                this.videoElement.srcObject = this.localStream;
                console.log("تم الوصول إلى الكاميرا بنجاح");
                
            } catch (error) {
                console.error("خطأ في الوصول إلى الكاميرا:", error);
                this.showError();
                this.fallbackToLegacyStream(exerciseId);
                return;
            }
            
            // إنشاء اتصال نظير
            this.peerConnection = new RTCPeerConnection(this.config);
            console.log('تم إنشاء RTCPeerConnection');
            
            // إضافة تدفق محلي إلى اتصال النظير
            this.localStream.getTracks().forEach(track => {
                this.peerConnection.addTrack(track, this.localStream);
            });
            console.log('تمت إضافة المسارات المحلية إلى اتصال النظير');
            
            // إعداد معالجة مرشح ICE
            this.peerConnection.onicecandidate = (event) => {
                if (event.candidate) {
                    console.log('مرشح ICE جديد:', event.candidate);
                    // في التنفيذ الحقيقي، سنرسل هذا إلى الخادم
                }
            };
            
            // معالجة حالة الاتصال
            this.peerConnection.oniceconnectionstatechange = () => {
                console.log('حالة اتصال ICE:', this.peerConnection.iceConnectionState);
                if (this.peerConnection.iceConnectionState === 'failed' || 
                    this.peerConnection.iceConnectionState === 'disconnected') {
                    console.warn('فشل اتصال ICE أو تم قطع الاتصال، جاري تجربة الخطة البديلة');
                    this.fallbackToLegacyStream(exerciseId);
                }
            };
            
            // معالجة التدفق البعيد
            this.peerConnection.ontrack = (event) => {
                console.log('تم استلام مسار بعيد');
                if (event.streams && event.streams[0]) {
                    this.videoElement.srcObject = event.streams[0];
                    this.hideLoading();
                    console.log('تم تعيين التدفق البعيد إلى عنصر الفيديو');
                }
            };
            
            // إنشاء عرض بقيود مناسبة
            const offerOptions = {
                offerToReceiveAudio: false,
                offerToReceiveVideo: true
            };
            
            console.log('جاري إنشاء العرض...');
            const offer = await this.peerConnection.createOffer(offerOptions);
            await this.peerConnection.setLocalDescription(offer);
            console.log('تم تعيين الوصف المحلي');
            
            console.log('جاري إرسال العرض إلى الخادم...');
            
            // إرسال العرض إلى الخادم والحصول على الرد
            try {
                const response = await this.sendOfferToServer(offer, exerciseId);
                console.log('تم استلام رد من الخادم:', response);
                
                // تعيين الوصف البعيد من الرد
                if (response && response.sdp) {
                    try {
                        console.log('جاري تعيين الوصف البعيد...');
                        await this.peerConnection.setRemoteDescription(
                            new RTCSessionDescription(response.sdp)
                        );
                        console.log('تم تعيين الوصف البعيد بنجاح');
                        
                        // إضافة مرشحات ICE من الرد
                        if (response.ice_candidates && response.ice_candidates.length > 0) {
                            console.log(`إضافة ${response.ice_candidates.length} مرشح ICE...`);
                            for (const candidate of response.ice_candidates) {
                                try {
                                    await this.peerConnection.addIceCandidate(
                                        new RTCIceCandidate(candidate)
                                    );
                                    console.log('تمت إضافة مرشح ICE');
                                } catch (iceCandidateError) {
                                    console.error('خطأ في إضافة مرشح ICE:', iceCandidateError);
                                }
                            }
                        }
                        
                        console.log('تم إكمال إعداد اتصال WebRTC');
                        this.hideLoading();
                        return true;
                    } catch (sdpError) {
                        console.error('خطأ في تعيين الوصف البعيد:', sdpError);
                        this.fallbackToLegacyStream(exerciseId);
                    }
                } else {
                    console.error('تنسيق رد غير صالح من الخادم');
                    this.fallbackToLegacyStream(exerciseId);
                }
            } catch (serverError) {
                console.error('خطأ في الاتصال بالخادم:', serverError);
                this.fallbackToLegacyStream(exerciseId);
            }
            
        } catch (error) {
            console.error('خطأ في تهيئة اتصال WebRTC:', error);
            this.fallbackToLegacyStream(exerciseId);
        }
        
        return false;
    }
    
    /**
     * الرجوع إلى طريقة البث التقليدية
     * @param {string} exerciseId - معرف التمرين للبث
     */
    fallbackToLegacyStream(exerciseId) {
        console.log('الرجوع إلى بث الفيديو التقليدي لـ:', exerciseId);
        this.resetConnection();
        
        try {
            this.showLegacyStream(exerciseId);
            return true;
        } catch (error) {
            console.error('خطأ في إعداد البث التقليدي:', error);
            this.showError();
            return false;
        }
    }
    
    /**
     * إعداد بث فيديو تقليدي باستخدام multipart/x-mixed-replace
     * @param {string} exerciseId - معرف التمرين للبث
     */
    showLegacyStream(exerciseId) {
        console.log('إعداد البث التقليدي لـ:', exerciseId);
        
        // مسح أي مصدر فيديو موجود
        if (this.videoElement && this.videoElement.srcObject) {
            const tracks = this.videoElement.srcObject.getTracks();
            tracks.forEach(track => track.stop());
            this.videoElement.srcObject = null;
        }
        
        // إنشاء عنصر صورة للبث التقليدي
        const imgElement = document.createElement('img');
        imgElement.style.width = '100%';
        imgElement.style.height = '100%';
        imgElement.style.objectFit = 'cover';
        imgElement.src = `/video_feed/${exerciseId}`;
        console.log('تم تعيين مصدر الصورة إلى:', `/video_feed/${exerciseId}`);
        
        // استبدال الفيديو بالصورة
        const videoContainer = document.getElementById('video-container');
        
        // تذكر زر ملء الشاشة إذا كان موجودًا
        const controlsElement = videoContainer.querySelector('.video-controls');
        const statusBadge = videoContainer.querySelector('.status-badge');
        
        // مسح المحتوى
        videoContainer.innerHTML = '';
        
        // إضافة الصورة
        videoContainer.appendChild(imgElement);
        
        // إعادة إضافة عناصر التحكم والشارات إذا كانت موجودة
        if (statusBadge) videoContainer.appendChild(statusBadge);
        if (controlsElement) videoContainer.appendChild(controlsElement);
        
        this.hideLoading();
        console.log('تم التبديل إلى وضع البث التقليدي بنجاح');
    }
    
    /**
     * إرسال عرض إلى الخادم والحصول على رد
     * @param {RTCSessionDescriptionInit} offer - عرض WebRTC
     * @param {string} exerciseId - معرف التمرين للبث
     * @returns {Promise<object>} - رد الخادم
     */
    async sendOfferToServer(offer, exerciseId) {
        console.log('إرسال عرض إلى الخادم للتمرين:', exerciseId);
        
        try {
            const response = await fetch('/api/rtc_offer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    sdp: offer,
                    exercise: exerciseId
                })
            });
            
            if (!response.ok) {
                console.error(`رد الخادم بحالة: ${response.status}`);
                throw new Error(`Server responded with status: ${response.status}`);
            }
            
            const jsonResponse = await response.json();
            console.log('تم استلام رد الخادم');
            return jsonResponse;
        } catch (error) {
            console.error('خطأ في إرسال العرض إلى الخادم:', error);
            throw error;
        }
    }
    
    /**
     * إعادة ضبط اتصال WebRTC
     */
    resetConnection() {
        console.log('إعادة ضبط اتصال WebRTC');
        
        if (this.peerConnection) {
            this.peerConnection.close();
            this.peerConnection = null;
            console.log('تم إغلاق اتصال النظير');
        }
        
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => {
                track.stop();
                console.log('تم إيقاف المسار المحلي');
            });
            this.localStream = null;
        }
        
        if (this.videoElement && this.videoElement.srcObject) {
            const tracks = this.videoElement.srcObject.getTracks();
            tracks.forEach(track => {
                track.stop();
                console.log('تم إيقاف مسار عنصر الفيديو');
            });
            this.videoElement.srcObject = null;
        }
        
        this.currentExercise = null;
        console.log('تم إكمال إعادة ضبط الاتصال');
    }
    
    /**
     * إظهار مؤشر التحميل
     */
    showLoading() {
        console.log('إظهار مؤشر التحميل');
        if (this.loadingIndicator) this.loadingIndicator.classList.remove('d-none');
        if (this.errorMessage) this.errorMessage.classList.add('d-none');
        if (this.noExercise) this.noExercise.classList.add('d-none');
    }
    
    /**
     * إخفاء مؤشر التحميل
     */
    hideLoading() {
        console.log('إخفاء مؤشر التحميل');
        if (this.loadingIndicator) this.loadingIndicator.classList.add('d-none');
    }
    
    /**
     * إظهار رسالة خطأ
     */
    showError() {
        console.log('إظهار رسالة خطأ');
        if (this.loadingIndicator) this.loadingIndicator.classList.add('d-none');
        if (this.errorMessage) this.errorMessage.classList.remove('d-none');
        if (this.noExercise) this.noExercise.classList.add('d-none');
    }
    
    /**
     * إظهار رسالة عدم تحديد التمرين
     */
    showNoExercise() {
        console.log('إظهار رسالة عدم وجود تمرين');
        if (this.loadingIndicator) this.loadingIndicator.classList.add('d-none');
        if (this.errorMessage) this.errorMessage.classList.add('d-none');
        if (this.noExercise) this.noExercise.classList.remove('d-none');
    }
}

// إنشاء نسخة عالمية من معالج WebRTC
console.log('إنشاء نسخة عالمية من معالج WebRTC');
window.rtcHandler = new WebRTCHandler();