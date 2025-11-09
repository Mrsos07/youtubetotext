/**
 * PDF Export Utility - نظام تصدير PDF محسّن وموحد
 * يعمل في الصفحة الرئيسية وصفحة ملفاتي
 */

/**
 * تصدير البيانات إلى PDF بتنسيق محسّن
 * @param {Object} data - بيانات الفيديو
 * @param {string} data.videoTitle - عنوان الفيديو
 * @param {string} data.videoUrl - رابط الفيديو
 * @param {string} data.introduction - المقدمة
 * @param {string} data.summary - الملخص
 * @param {string} data.mainPoints - أهم النقاط
 * @param {string} data.fullContent - المحتوى الكامل
 */
async function exportToPDF(data) {
    try {
        // التحقق من وجود البيانات
        if (!data) {
            throw new Error('لا توجد بيانات للتصدير');
        }

        // استخراج البيانات مع القيم الافتراضية - دعم جميع الأسماء الممكنة
        const title = data.videoTitle || data.video_title || data.output?.subject || data.title || 'تفريغ محتوى يوتيوب';
        const videoUrl = data.video_url || data.videoUrl || data.url || '';
        const introduction = data.introduction || data.output?.introduction || '';
        const summary = data.summary || '';
        const mainPoints = data.mainPoints || data.main_points || '';
        const fullContent = data.fullContent || data.full_content || data.fullcontent || '';
        
        console.log('📄 PDF Export Data:', { title, videoUrl, introduction: !!introduction, summary: !!summary, mainPoints: !!mainPoints, fullContent: !!fullContent });

        // إنشاء محتوى HTML محسّن
        const htmlContent = createPDFContent({
            title,
            videoUrl,
            introduction,
            summary,
            mainPoints,
            fullContent
        });

        // إنشاء عنصر مؤقت
        const element = document.createElement('div');
        element.innerHTML = htmlContent;
        
        // إضافة العنصر للصفحة مؤقتاً (مطلوب لـ html2canvas)
        element.style.position = 'absolute';
        element.style.left = '-9999px';
        document.body.appendChild(element);

        // إعدادات PDF محسّنة
        const opt = {
            margin: [15, 15, 15, 15],
            filename: sanitizeFilename(title) + '.pdf',
            image: { 
                type: 'jpeg', 
                quality: 0.98 
            },
            html2canvas: { 
                scale: 2,
                useCORS: true,
                letterRendering: true,
                logging: false,
                backgroundColor: '#ffffff'
            },
            jsPDF: { 
                unit: 'mm', 
                format: 'a4', 
                orientation: 'portrait',
                compress: true
            },
            pagebreak: { 
                mode: ['avoid-all', 'css', 'legacy'],
                before: '.page-break-before',
                after: '.page-break-after'
            }
        };

        // تصدير PDF
        await html2pdf().set(opt).from(element).save();
        
        // إزالة العنصر المؤقت
        document.body.removeChild(element);
        
        console.log('✅ تم تصدير PDF بنجاح');
        
    } catch (error) {
        console.error('❌ خطأ في تصدير PDF:', error);
        alert('حدث خطأ في تصدير PDF. يرجى المحاولة مرة أخرى.');
        throw error;
    }
}

/**
 * إنشاء محتوى HTML للـ PDF
 */
function createPDFContent({ title, videoUrl, introduction, summary, mainPoints, fullContent }) {
    return `
        <div style="font-family: 'Tajawal', 'Arial', sans-serif; direction: rtl; color: #000; line-height: 1.9;">
            <!-- Header -->
            <div style="text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 3px solid #FF0000;">
                <h1 style="font-size: 26px; font-weight: bold; color: #FF0000; margin: 0 0 15px 0;">
                    ${escapeHtml(title)}
                </h1>
                ${videoUrl ? `
                    <div style="margin-top: 10px;">
                        <p style="font-size: 11px; color: #666; margin: 5px 0;">
                            <strong>رابط الفيديو:</strong>
                        </p>
                        <p style="font-size: 10px; color: #0066cc; word-break: break-all; margin: 0;">
                            ${escapeHtml(videoUrl)}
                        </p>
                    </div>
                ` : ''}
                <p style="font-size: 10px; color: #999; margin-top: 15px;">
                    تم التصدير بواسطة YouTube Transcript • ${new Date().toLocaleDateString('ar-EG')}
                </p>
            </div>

            <!-- Introduction -->
            ${introduction ? `
                <div style="margin-bottom: 25px; page-break-inside: avoid;">
                    <h2 style="font-size: 20px; font-weight: bold; color: #FF0000; border-bottom: 2px solid #FF0000; padding-bottom: 8px; margin-bottom: 15px;">
                        📝 المقدمة
                    </h2>
                    <div style="font-size: 14px; text-align: justify; line-height: 2; padding: 10px; background-color: #f9f9f9; border-right: 4px solid #FF0000;">
                        ${formatText(introduction)}
                    </div>
                </div>
            ` : ''}

            <!-- Summary -->
            ${summary ? `
                <div style="margin-bottom: 25px; page-break-inside: avoid;">
                    <h2 style="font-size: 20px; font-weight: bold; color: #FF0000; border-bottom: 2px solid #FF0000; padding-bottom: 8px; margin-bottom: 15px;">
                        📊 الملخص
                    </h2>
                    <div style="font-size: 14px; text-align: justify; line-height: 2; padding: 10px; background-color: #fff8f0; border-right: 4px solid #FFA500;">
                        ${formatText(summary)}
                    </div>
                </div>
            ` : ''}

            <!-- Main Points -->
            ${mainPoints ? `
                <div style="margin-bottom: 25px; page-break-inside: avoid;">
                    <h2 style="font-size: 20px; font-weight: bold; color: #FF0000; border-bottom: 2px solid #FF0000; padding-bottom: 8px; margin-bottom: 15px;">
                        ⭐ أهم النقاط
                    </h2>
                    <div style="font-size: 14px; text-align: justify; line-height: 2; padding: 10px; background-color: #f0f8ff; border-right: 4px solid #0066cc;">
                        ${formatPoints(mainPoints)}
                    </div>
                </div>
            ` : ''}

            <!-- Full Content -->
            ${fullContent ? `
                <div style="margin-bottom: 25px;" class="page-break-before">
                    <h2 style="font-size: 20px; font-weight: bold; color: #FF0000; border-bottom: 2px solid #FF0000; padding-bottom: 8px; margin-bottom: 15px;">
                        📄 المحتوى الكامل
                    </h2>
                    <div style="font-size: 12px; text-align: justify; line-height: 1.9; padding: 10px; background-color: #fafafa;">
                        ${formatText(fullContent)}
                    </div>
                </div>
            ` : ''}

            <!-- Footer -->
            <div style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #ddd; text-align: center;">
                <p style="font-size: 10px; color: #999;">
                    صُنع بإتقان © 2025 • YouTube Transcript
                </p>
            </div>
        </div>
    `;
}

/**
 * تنسيق النص مع فواصل الأسطر
 */
function formatText(text) {
    if (!text) return '';
    return escapeHtml(text)
        .replace(/\n\n/g, '</p><p style="margin: 10px 0;">')
        .replace(/\n/g, '<br>');
}

/**
 * تنسيق النقاط مع تمييز الأرقام والرموز
 */
function formatPoints(text) {
    if (!text) return '';
    
    let formatted = escapeHtml(text);
    
    // تمييز النقاط المرقمة (1. أو 1- أو ١.)
    formatted = formatted.replace(/^(\d+[\.\-\)]|[•\-\*])\s*/gm, 
        '<strong style="color: #FF0000; font-size: 16px;">$1</strong> ');
    
    // تمييز النقاط بالأرقام العربية
    formatted = formatted.replace(/^([٠-٩]+[\.\-\)])\s*/gm, 
        '<strong style="color: #FF0000; font-size: 16px;">$1</strong> ');
    
    // فواصل الأسطر
    formatted = formatted.replace(/\n/g, '<br>');
    
    return formatted;
}

/**
 * تنظيف اسم الملف
 */
function sanitizeFilename(filename) {
    return filename
        .substring(0, 50) // حد أقصى 50 حرف
        .replace(/[<>:"/\\|?*]/g, '') // إزالة الأحرف غير المسموحة
        .replace(/\s+/g, '_') // استبدال المسافات بـ _
        .trim();
}

/**
 * تحويل HTML entities لمنع XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * تصدير من الصفحة الرئيسية
 * @param {Object} currentData - البيانات الحالية
 */
async function exportPDF(currentData) {
    if (!currentData) {
        alert('لا توجد بيانات للتصدير. يرجى تفريغ فيديو أولاً.');
        return;
    }
    
    await exportToPDF(currentData);
}

/**
 * تصدير من صفحة ملفاتي
 * @param {number} transcriptId - معرف النسخة
 */
async function exportTranscriptPDF(transcriptId) {
    try {
        // عرض مؤشر التحميل
        const loadingMsg = showLoadingMessage('جاري تصدير PDF...');
        
        // جلب البيانات من API
        const response = await fetch(`/api/transcript/${transcriptId}`);
        
        if (!response.ok) {
            throw new Error('فشل في تحميل البيانات');
        }
        
        const data = await response.json();
        
        // تصدير PDF
        await exportToPDF(data);
        
        // إزالة مؤشر التحميل
        hideLoadingMessage(loadingMsg);
        
    } catch (error) {
        console.error('Error:', error);
        
        // إزالة مؤشر التحميل إذا كان موجوداً
        const loadingMsg = document.getElementById('pdf-loading');
        if (loadingMsg) {
            document.body.removeChild(loadingMsg);
        }
        
        alert('حدث خطأ في تصدير PDF: ' + error.message);
    }
}

/**
 * تصدير إلى Word/Text
 * @param {number} transcriptId - معرف النسخة
 */
async function exportTranscriptWord(transcriptId) {
    try {
        // عرض مؤشر التحميل
        const loadingMsg = showLoadingMessage('جاري تصدير Word...');
        
        // جلب البيانات من API
        const response = await fetch(`/api/transcript/${transcriptId}`);
        
        if (!response.ok) {
            throw new Error('فشل في تحميل البيانات');
        }
        
        const data = await response.json();
        
        // استخراج البيانات
        const title = data.videoTitle || data.video_title || 'تفريغ محتوى يوتيوب';
        const videoUrl = data.video_url || data.videoUrl || '';
        const introduction = data.introduction || '';
        const summary = data.summary || '';
        const mainPoints = data.mainPoints || data.main_points || '';
        const fullContent = data.fullContent || data.full_content || '';
        
        // إنشاء محتوى النص
        let content = `${title}\n\n`;
        content += '═══════════════════════════════════════\n\n';
        
        if (videoUrl) {
            content += `رابط الفيديو:\n${videoUrl}\n\n`;
            content += '═══════════════════════════════════════\n\n';
        }
        
        if (introduction) {
            content += `📝 المقدمة:\n${introduction}\n\n`;
            content += '═══════════════════════════════════════\n\n';
        }
        
        if (summary) {
            content += `📊 الملخص:\n${summary}\n\n`;
            content += '═══════════════════════════════════════\n\n';
        }
        
        if (mainPoints) {
            content += `⭐ أهم النقاط:\n${mainPoints}\n\n`;
            content += '═══════════════════════════════════════\n\n';
        }
        
        if (fullContent) {
            content += `📄 المحتوى الكامل:\n${fullContent}`;
        }
        
        // إنشاء وتنزيل الملف
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = sanitizeFilename(title) + '.txt';
        a.click();
        URL.revokeObjectURL(url);
        
        // إزالة مؤشر التحميل
        hideLoadingMessage(loadingMsg);
        
        console.log('✅ تم تصدير Word بنجاح');
        
    } catch (error) {
        console.error('Error:', error);
        
        // إزالة مؤشر التحميل
        const loadingMsg = document.getElementById('export-loading');
        if (loadingMsg) {
            hideLoadingMessage(loadingMsg);
        }
        
        alert('حدث خطأ في تصدير Word: ' + error.message);
    }
}

/**
 * عرض رسالة تحميل
 */
function showLoadingMessage(message) {
    const loadingMsg = document.createElement('div');
    loadingMsg.id = 'export-loading';
    loadingMsg.innerHTML = `
        <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                    background: rgba(0,0,0,0.9); color: white; padding: 25px 50px; 
                    border-radius: 12px; z-index: 10000; text-align: center; box-shadow: 0 8px 32px rgba(0,0,0,0.5);">
            <div style="font-size: 20px; margin-bottom: 10px; font-weight: bold;">${message}</div>
            <div style="font-size: 14px; color: #ccc;">يرجى الانتظار...</div>
        </div>
    `;
    document.body.appendChild(loadingMsg);
    return loadingMsg;
}

/**
 * إخفاء رسالة التحميل
 */
function hideLoadingMessage(element) {
    if (element && element.parentNode) {
        element.parentNode.removeChild(element);
    }
}

// تصدير الدوال للاستخدام العام
if (typeof window !== 'undefined') {
    window.exportPDF = exportPDF;
    window.exportTranscriptPDF = exportTranscriptPDF;
    window.exportTranscriptWord = exportTranscriptWord;
    window.exportToPDF = exportToPDF;
}
