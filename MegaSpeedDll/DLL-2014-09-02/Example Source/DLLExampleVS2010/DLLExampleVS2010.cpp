
// DLLExampleVS2010.cpp : Defines the class behaviors for the application.
//

#include "stdafx.h"
#include "DLLExampleVS2010.h"
#include "DLLExampleVS2010Dlg.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#endif


// CDLLExampleVS2010App

BEGIN_MESSAGE_MAP(CDLLExampleVS2010App, CWinApp)
	ON_COMMAND(ID_HELP, &CWinApp::OnHelp)
END_MESSAGE_MAP()


//for tracking memory leaks in this application
#ifdef _DEBUG
class MemStateHolder
{
public:
    _CrtMemState m_ms;
    MemStateHolder()    {	_CrtMemCheckpoint(&m_ms);		}
    ~MemStateHolder()	{_CrtMemDumpAllObjectsSince(&m_ms);	}
} g_MemStateHolder;
#endif


// CDLLExampleVS2010App construction

CDLLExampleVS2010App::CDLLExampleVS2010App()
{
#ifdef _DEBUG
	AfxEnableMemoryLeakDump(FALSE);
#endif
	// TODO: add construction code here,
	// Place all significant initialization in InitInstance
}


// The one and only CDLLExampleVS2010App object

CDLLExampleVS2010App theApp;


// CDLLExampleVS2010App initialization

BOOL CDLLExampleVS2010App::InitInstance()
{
	// InitCommonControlsEx() is required on Windows XP if an application
	// manifest specifies use of ComCtl32.dll version 6 or later to enable
	// visual styles.  Otherwise, any window creation will fail.
	INITCOMMONCONTROLSEX InitCtrls;
	InitCtrls.dwSize = sizeof(InitCtrls);
	// Set this to include all the common control classes you want to use
	// in your application.
	InitCtrls.dwICC = ICC_WIN95_CLASSES;
	InitCommonControlsEx(&InitCtrls);

	CWinApp::InitInstance();


	// Create the shell manager, in case the dialog contains
	// any shell tree view or shell list view controls.
	CShellManager *pShellManager = new CShellManager;

	// Standard initialization
	// If you are not using these features and wish to reduce the size
	// of your final executable, you should remove from the following
	// the specific initialization routines you do not need
	// Change the registry key under which our settings are stored
	// TODO: You should modify this string to be something appropriate
	// such as the name of your company or organization
	SetRegistryKey(_T("Local AppWizard-Generated Applications"));

	CDLLExampleVS2010Dlg dlg;
	m_pMainWnd = &dlg;
	INT_PTR nResponse = dlg.DoModal();
	if (nResponse == IDOK)
	{
		// TODO: Place code here to handle when the dialog is
		//  dismissed with OK
	}
	else if (nResponse == IDCANCEL)
	{
		// TODO: Place code here to handle when the dialog is
		//  dismissed with Cancel
	}

	// Delete the shell manager created above.
	if (pShellManager != NULL)
	{
		delete pShellManager;
	}

	// Since the dialog has been closed, return FALSE so that we exit the
	//  application, rather than start the application's message pump.
	return FALSE;
}

