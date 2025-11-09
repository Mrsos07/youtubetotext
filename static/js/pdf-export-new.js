/**
 * PDF Export Utility - نظام تصدير PDF مع دعم كامل للعربية
 * يستخدم html2canvas + jsPDF لضمان عرض صحيح للنصوص العربية
 */

/**
 * تصدير البيانات إلى PDF
 */
async function exportToPDF(data) {
    try {
        console.log('🔍 Starting PDF export with data:', data);
        
        if (!data) {
            throw new Error('لا توجد بيانات للتصدير');
        }

        // استخراج البيانات
        const title = data.videoTitle || data.video_title || data.title || 'تفريغ محتوى يوتيوب';
        const videoUrl = data.video_url || data.videoUrl || data.url || '';
        const introduction = data.introduction || '';
        const summary = data.summary || '';
        const mainPoints = data.mainPoints || data.main_points || '';
        const fullContent = data.fullContent || data.full_content || '';

        console.log('📊 Extracted data:', {
            title,
            hasVideoUrl: !!videoUrl,
            hasIntroduction: !!introduction,
            hasSummary: !!summary,
            hasMainPoints: !!mainPoints,
            hasFullContent: !!fullContent,
            introLength: introduction?.length,
            summaryLength: summary?.length,
            mainPointsLength: mainPoints?.length,
            fullContentLength: fullContent?.length
        });

        // إنشاء HTML للمحتوى
        const htmlContent = createPDFHTML(title, videoUrl, introduction, summary, mainPoints, fullContent);
        
        // إنشاء عنصر مؤقت
        const container = document.createElement('div');
        container.innerHTML = htmlContent;
        container.style.position = 'absolute';
        container.style.left = '-9999px';
        container.style.top = '0';
        container.style.width = '210mm'; // A4 width
        container.style.padding = '15mm';
        container.style.backgroundColor = 'white';
        container.style.fontFamily = 'Tajawal, Arial, sans-serif';
        document.body.appendChild(container);

        // الانتظار قليلاً لضمان تحميل الخطوط
        await new Promise(resolve => setTimeout(resolve, 100));

        // تحويل HTML إلى Canvas
        const canvas = await html2canvas(container, {
            scale: 2,
            useCORS: true,
            logging: false,
            backgroundColor: '#ffffff',
            windowWidth: 794, // A4 width in pixels at 96 DPI
            windowHeight: container.scrollHeight
        });

        // إزالة العنصر المؤقت
        document.body.removeChild(container);

        // إنشاء PDF
        const { jsPDF } = window.jspdf;
        const imgWidth = 210; // A4 width in mm
        const pageHeight = 297; // A4 height in mm
        const imgHeight = (canvas.height * imgWidth) / canvas.width;
        let heightLeft = imgHeight;
        let position = 0;

        const pdf = new jsPDF('p', 'mm', 'a4');
        const imgData = canvas.toDataURL('image/jpeg', 0.95);

        // إضافة الصفحة الأولى
        pdf.addImage(imgData, 'JPEG', 0, position, imgWidth, imgHeight);
        heightLeft -= pageHeight;

        // إضافة صفحات إضافية إذا لزم الأمر
        while (heightLeft > 0) {
            position = heightLeft - imgHeight;
            pdf.addPage();
            pdf.addImage(imgData, 'JPEG', 0, position, imgWidth, imgHeight);
            heightLeft -= pageHeight;
        }

        // حفظ الملف
        const filename = sanitizeFilename(title) + '.pdf';
        pdf.save(filename);
        
        console.log('✅ PDF exported successfully:', filename);
        return true;

    } catch (error) {
        console.error('❌ PDF Export Error:', error);
        alert('حدث خطأ في تصدير PDF: ' + error.message);
        throw error;
    }
}

/**
 * إنشاء HTML للمحتوى
 */
function createPDFHTML(title, videoUrl, introduction, summary, mainPoints, fullContent) {
    return `
        <div style="font-family: 'Tajawal', Arial, sans-serif; direction: rtl; color: #000; line-height: 1.8;">
            <!-- العنوان -->
            <div style="text-align: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 3px solid #FF0000;">
                <h1 style="font-size: 24px; font-weight: bold; color: #FF0000; margin: 0;">
                    ${escapeHtml(title)}
                </h1>
                ${videoUrl ? `
                    <div style="margin-top: 10px;">
                        <p style="font-size: 10px; color: #666; margin: 5px 0;">
                            <strong>رابط الفيديو:</strong>
                        </p>
                        <p style="font-size: 9px; color: #0066cc; word-break: break-all; margin: 0;">
                            ${escapeHtml(videoUrl)}
                        </p>
                    </div>
                ` : ''}
                <p style="font-size: 9px; color: #999; margin-top: 10px;">
                    تم التصدير بواسطة YouTube Transcript • ${new Date().toLocaleDateString('ar-EG')}
                </p>
            </div>

            ${introduction ? `
                <div style="margin-bottom: 20px; page-break-inside: avoid;">
                    <h2 style="font-size: 18px; font-weight: bold; color: #FF0000; border-bottom: 2px solid #FF0000; padding-bottom: 5px; margin-bottom: 10px;">
                        📝 المقدمة
                    </h2>
                    <div style="font-size: 13px; text-align: justify; line-height: 1.9; padding: 10px; background-color: #f9f9f9; border-right: 4px solid #FF0000;">
                        ${formatText(introduction)}
                    </div>
                </div>
            ` : ''}

            ${summary ? `
                <div style="margin-bottom: 20px; page-break-inside: avoid;">
                    <h2 style="font-size: 18px; font-weight: bold; color: #FF0000; border-bottom: 2px solid #FF0000; padding-bottom: 5px; margin-bottom: 10px;">
                        📊 الملخص
                    </h2>
                    <div style="font-size: 13px; text-align: justify; line-height: 1.9; padding: 10px; background-color: #fff8f0; border-right: 4px solid #FFA500;">
                        ${formatText(summary)}
                    </div>
                </div>
            ` : ''}

            ${mainPoints ? `
                <div style="margin-bottom: 20px; page-break-inside: avoid;">
                    <h2 style="font-size: 18px; font-weight: bold; color: #FF0000; border-bottom: 2px solid #FF0000; padding-bottom: 5px; margin-bottom: 10px;">
                        ⭐ أهم النقاط
                    </h2>
                    <div style="font-size: 13px; text-align: justify; line-height: 1.9; padding: 10px; background-color: #f0f8ff; border-right: 4px solid #0066cc;">
                        ${formatText(mainPoints)}
                    </div>
                </div>
            ` : ''}

            ${fullContent ? `
                <div style="margin-bottom: 20px;">
                    <h2 style="font-size: 18px; font-weight: bold; color: #FF0000; border-bottom: 2px solid #FF0000; padding-bottom: 5px; margin-bottom: 10px;">
                        📄 المحتوى الكامل
                    </h2>
                    <div style="font-size: 11px; text-align: justify; line-height: 1.8; padding: 10px; background-color: #fafafa;">
                        ${formatText(fullContent)}
                    </div>
                </div>
            ` : ''}

            <!-- Footer -->
            <div style="margin-top: 30px; padding-top: 15px; border-top: 2px solid #ddd; text-align: center;">
                <p style="font-size: 9px; color: #999;">
                    صُنع بإتقان © 2025 • YouTube Transcript
                </p>
            </div>
        </div>
    `;
}

/**
 * تنسيق النص
 */
function formatText(text) {
    if (!text) return '';
    return escapeHtml(text).replace(/\n/g, '<br>');
}

/**
 * تحويل HTML entities
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * تصدير من الصفحة الرئيسية
 */
async function exportPDF(currentData) {
    if (!currentData) {
        alert('لا توجد بيانات للتصدير. يرجى تفريغ فيديو أولاً.');
        return;
    }
    
    const loadingMsg = showLoadingMessage('جاري تصدير PDF...');
    try {
        await exportToPDF(currentData);
        hideLoadingMessage(loadingMsg);
    } catch (error) {
        hideLoadingMessage(loadingMsg);
    }
}

/**
 * تصدير من صفحة ملفاتي
 */
async function exportTranscriptPDF(transcriptId) {
    const loadingMsg = showLoadingMessage('جاري تحميل البيانات...');
    
    try {
        console.log('📥 Fetching transcript:', transcriptId);
        
        const response = await fetch(`/api/transcript/${transcriptId}`);
        
        if (!response.ok) {
            throw new Error('فشل في تحميل البيانات من السيرفر');
        }
        
        const data = await response.json();
        console.log('📦 Received data:', data);
        
        hideLoadingMessage(loadingMsg);
        
        const exportLoadingMsg = showLoadingMessage('جاري إنشاء PDF...');
        await exportToPDF(data);
        hideLoadingMessage(exportLoadingMsg);
        
    } catch (error) {
        console.error('❌ Error:', error);
        hideLoadingMessage(loadingMsg);
        alert('حدث خطأ: ' + error.message);
    }
}

/**
 * تصدير Word/Text
 */
async function exportTranscriptWord(transcriptId) {
    const loadingMsg = showLoadingMessage('جاري تصدير Word...');
    
    try {
        const response = await fetch(`/api/transcript/${transcriptId}`);
        
        if (!response.ok) {
            throw new Error('فشل في تحميل البيانات');
        }
        
        const data = await response.json();
        
        const title = data.videoTitle || data.video_title || 'تفريغ محتوى يوتيوب';
        const videoUrl = data.video_url || data.videoUrl || '';
        const introduction = data.introduction || '';
        const summary = data.summary || '';
        const mainPoints = data.mainPoints || data.main_points || '';
        const fullContent = data.fullContent || data.full_content || '';
        
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
        
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = sanitizeFilename(title) + '.txt';
        a.click();
        URL.revokeObjectURL(url);
        
        hideLoadingMessage(loadingMsg);
        console.log('✅ Word exported successfully');
        
    } catch (error) {
        console.error('Error:', error);
        hideLoadingMessage(loadingMsg);
        alert('حدث خطأ في تصدير Word: ' + error.message);
    }
}

/**
 * تنظيف اسم الملف
 */
function sanitizeFilename(filename) {
    return filename
        .substring(0, 50)
        .replace(/[<>:"/\\|?*]/g, '')
        .replace(/\s+/g, '_')
        .trim();
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
