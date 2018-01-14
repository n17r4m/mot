// DisplayWnd.cpp : implementation file
//

#include "stdafx.h"
#include "DisplayWnd.h"


// CDisplayWnd

IMPLEMENT_DYNAMIC(CDisplayWnd, CWnd)

CDisplayWnd::CDisplayWnd()
{
	DisplayData	= NULL;

	ImgWidth	= 0;
	ImgHeight	= 0;

	ScaleW = 1.0f;
	ScaleH = 1.0f;

	HScrollPos = 0;
	VScrollPos = 0;
}

CDisplayWnd::~CDisplayWnd()
{
	if(DisplayData != NULL)
	{
		delete[] DisplayData;
		DisplayData = NULL;
	}
}


BEGIN_MESSAGE_MAP(CDisplayWnd, CWnd)
	ON_WM_PAINT()
	ON_WM_ERASEBKGND()
	ON_WM_HSCROLL()
	ON_WM_VSCROLL()
	ON_WM_SIZE()
END_MESSAGE_MAP()


void CDisplayWnd::SetInputData8Bit(int Width, int Height, const unsigned __int8 *InputRawData)
{
	if(this->ImgWidth != Width || this->ImgHeight != Height)
		UpdateInputSize(Width, Height);

	ProcessRawData(InputRawData);
	Invalidate();
}
void CDisplayWnd::SetInputData32Bit(int Width, int Height, const unsigned __int32 *InputData)
{
	if(this->ImgWidth != Width || this->ImgHeight != Height)
		UpdateInputSize(Width, Height);

	memcpy(DisplayData, InputData, ImgWidth*ImgHeight*4);
	DisplayBmp.SetBitmapBits(ImgWidth*ImgHeight*4, DisplayData);
	Invalidate();
}

void CDisplayWnd::ProcessRawData(const unsigned __int8 *RawData)
{
	for(int y=0; y<ImgHeight; y++)
	{
		for(int x=0; x<ImgWidth; x++)
		{
			//for 8 bit grayscale data, just expand it to 32 bit for display
			BYTE Gray = RawData[y*ImgWidth + x];

			DisplayData[y*ImgWidth + x] = RGB(Gray, Gray, Gray);

			//for colour data, would need to interpolate colours according to the bayer pattern of the sensor
			//eg:
			//[G R G R ...]
			//[B G B G ...]
			//[G R G R ...]
			//[...]
		}
	}

	DisplayBmp.SetBitmapBits(ImgWidth*ImgHeight*4, DisplayData);
}

void CDisplayWnd::UpdateInputSize(int Width, int Height)
{
	ImgWidth	 = Width;
	ImgHeight	 = Height;

	if(DisplayData != NULL)
		delete[] DisplayData;

	DisplayData = new unsigned __int32[ImgWidth*ImgHeight];	//32 bit data for display

	DisplayBmp.DeleteObject();
	DisplayBmp.CreateBitmap(ImgWidth, ImgHeight, 1, 32, DisplayData);

	UpdateScrollBars();
}

void CDisplayWnd::UpdateScrollBars()
{
	int ScaledWidth		= (int)(ImgWidth * ScaleW);
	int ScaledHeight	= (int)(ImgHeight* ScaleH);

	int ExtraW = ScaledWidth - DispWidth;
	int ExtraH = ScaledHeight- DispHeight;
	if(ExtraW < 0)	ExtraW = 0;
	if(ExtraH < 0)	ExtraH = 0;

	HScrollPos = min(ExtraW, HScrollPos);
	VScrollPos = min(ExtraH, VScrollPos);

	SCROLLINFO ScrollInfo;
	ZeroMemory(&ScrollInfo, sizeof(SCROLLINFO));
	ScrollInfo.cbSize = sizeof(SCROLLINFO);
	ScrollInfo.fMask = SIF_PAGE | SIF_POS | SIF_RANGE;

	ScrollInfo.nMin		= 0;
	ScrollInfo.nMax		= ScaledWidth;//ExtraW;
	ScrollInfo.nPos		= HScrollPos;
	ScrollInfo.nPage	= DispWidth;
	SetScrollInfo(SB_HORZ, &ScrollInfo, TRUE);

	ScrollInfo.nMax		= ScaledHeight;//ExtraH;
	ScrollInfo.nPos		= VScrollPos;
	ScrollInfo.nPage	= DispHeight;
	SetScrollInfo(SB_VERT, &ScrollInfo, TRUE);
}


// CDisplayWnd message handlers

void CDisplayWnd::OnPaint()
{
	CPaintDC dc(this); // device context for painting

	CDC MemDC;
	MemDC.CreateCompatibleDC(&dc);
	MemDC.SelectObject(DisplayBmp);

	//copy the required portion of the bitmap to the part of the window that needs updating
	CRect UpdateRect	= dc.m_ps.rcPaint;
	int ImgSrcX = HScrollPos+UpdateRect.left;
	int ImgSrcY = VScrollPos+UpdateRect.top;

	int ImgWidthToUse	= min(UpdateRect.Width(), ImgWidth-ImgSrcX);
	int ImgHeightToUse	= min(UpdateRect.Height(), ImgHeight-ImgSrcY);

	dc.BitBlt(UpdateRect.left, UpdateRect.top, ImgWidthToUse, ImgHeightToUse, &MemDC, ImgSrcX, ImgSrcY, SRCCOPY);

	int ExtraW = UpdateRect.Width() - ImgWidthToUse;
	int ExtraH = UpdateRect.Height() - ImgHeightToUse;
	if(ExtraW > 0)
	{
		CRect FillRect(ImgWidthToUse, UpdateRect.top, UpdateRect.Width(), UpdateRect.Height());
		dc.FillSolidRect(&FillRect, RGB(0,0,0));
	}
	if(ExtraH > 0)
	{
		CRect FillRect(UpdateRect.left, ImgHeightToUse, UpdateRect.Width(), UpdateRect.Height());
		dc.FillSolidRect(&FillRect, RGB(0,0,0));
	}

	// Do not call CWnd::OnPaint() for painting messages
}


BOOL CDisplayWnd::OnEraseBkgnd(CDC* pDC)
{
	return TRUE;	//do nothing here to reduce flickering	
//	return CWnd::OnEraseBkgnd(pDC);
}

void CDisplayWnd::OnSize(UINT nType, int cx, int cy)
{
	CWnd::OnSize(nType, cx, cy);
	DispWidth	= cx;
	DispHeight	= cy;
	UpdateScrollBars();
}

void CDisplayWnd::OnHScroll(UINT nSBCode, UINT nPos, CScrollBar* pScrollBar)
{
	SCROLLINFO  ScrollInfo;
	GetScrollInfo(SB_HORZ, &ScrollInfo, SIF_ALL);

	int MinScrollVal = ScrollInfo.nMin;
	int MaxScrollVal = ScrollInfo.nMax-ScrollInfo.nPage-1;

	switch(nSBCode)
	{
	case SB_LEFT:		HScrollPos = MinScrollVal;	break;
	case SB_RIGHT:		HScrollPos = MaxScrollVal;	break;

	case SB_LINELEFT:	HScrollPos = max(MinScrollVal, HScrollPos - (DispWidth/4));	break;
	case SB_LINERIGHT:	HScrollPos = min(MaxScrollVal, HScrollPos + (DispWidth/4));	break;

	case SB_PAGELEFT:	HScrollPos = max(MinScrollVal, (int)(HScrollPos-ScrollInfo.nPage));	break;
	case SB_PAGERIGHT:	HScrollPos = min(MaxScrollVal, (int)(HScrollPos+ScrollInfo.nPage));	break;

	case SB_THUMBPOSITION:
	case SB_THUMBTRACK:
		HScrollPos = nPos;
		break;
	}

	SetScrollPos(SB_HORZ, HScrollPos, TRUE);

	ScrollWindowEx(ScrollInfo.nPos-HScrollPos, 0, NULL, NULL, NULL, NULL, SW_INVALIDATE);

	CWnd::OnHScroll(nSBCode, nPos, pScrollBar);
}

void CDisplayWnd::OnVScroll(UINT nSBCode, UINT nPos, CScrollBar* pScrollBar)
{
	SCROLLINFO  ScrollInfo;
	GetScrollInfo(SB_VERT, &ScrollInfo, SIF_ALL);

	int MinScrollVal = ScrollInfo.nMin;
	int MaxScrollVal = ScrollInfo.nMax-ScrollInfo.nPage-1;

	switch(nSBCode)
	{
	case SB_TOP:		VScrollPos = MinScrollVal;	break;
	case SB_BOTTOM:		VScrollPos = MaxScrollVal;	break;

	case SB_LINEUP:		VScrollPos = max(MinScrollVal, VScrollPos - (DispHeight/4));	break;
	case SB_LINEDOWN:	VScrollPos = min(MaxScrollVal, VScrollPos + (DispHeight/4));	break;

	case SB_PAGEUP:		VScrollPos = max(MinScrollVal, (int)(VScrollPos-ScrollInfo.nPage));	break;
	case SB_PAGEDOWN:	VScrollPos = min(MaxScrollVal, (int)(VScrollPos+ScrollInfo.nPage));	break;

	case SB_THUMBPOSITION:
	case SB_THUMBTRACK:
		VScrollPos = nPos;
		break;
	}

	SetScrollPos(SB_VERT, VScrollPos, TRUE);

	ScrollWindowEx(0, ScrollInfo.nPos-VScrollPos, NULL, NULL, NULL, NULL, SW_INVALIDATE);

	CWnd::OnVScroll(nSBCode, nPos, pScrollBar);
}