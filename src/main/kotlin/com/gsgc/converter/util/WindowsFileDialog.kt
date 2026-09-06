package com.gsgc.converter.util

import com.sun.jna.Pointer
import com.sun.jna.WString
import com.sun.jna.platform.win32.Guid
import com.sun.jna.platform.win32.Ole32
import com.sun.jna.platform.win32.WinDef
import com.sun.jna.platform.win32.WinNT
import com.sun.jna.platform.win32.WTypes
import com.sun.jna.platform.win32.COM.Unknown
import com.sun.jna.ptr.PointerByReference

/**
 * 现代 Windows 资源管理器样式文件/文件夹选择对话框。
 * 基于 COM IFileDialog 接口（Windows Vista+ 原生对话框，带面包屑地址栏、快速访问）。
 */
object WindowsFileDialog {

    private val CLSID_FileOpenDialog = Guid.GUID("DC1C5A9C-E88A-4DDE-A5A1-60F82A20AEF7")
    private val IID_IFileOpenDialog = Guid.IID("D57C7288-D4AD-4768-BE02-9D969532D960")

    // FILEOPENDIALOGOPTIONS flags
    private const val FOS_PICKFOLDERS = 0x00000020
    private const val FOS_FILEMUSTEXIST = 0x00001000
    private const val FOS_PATHMUSTEXIST = 0x00000800

    // SIGDN flags (0x80058000 溢出 Int，需 toInt)
    private const val SIGDN_FILESYSPATH = 0x80058000.toInt()

    private val CLSCTX_ALL = WTypes.CLSCTX_INPROC_SERVER or
            WTypes.CLSCTX_INPROC_HANDLER or
            WTypes.CLSCTX_LOCAL_SERVER

    /** RPC_E_CHANGED_MODE = 0x80010106，表示 COM 已以不同模式初始化 */
    private val RPC_E_CHANGED_MODE = WinNT.HRESULT(0x80010106.toInt())

    /**
     * 包装 IFileOpenDialog COM 对象，通过 vtable 索引调用方法。
     * vtable: IUnknown(0-2) -> IModalWindow.Show(3) -> IFileDialog(4-26)
     */
    private class FileOpenDialog(ptr: Pointer) : Unknown(ptr) {
        fun Show(hwnd: WinDef.HWND?): WinNT.HRESULT =
            _invokeNativeObject(3, arrayOf<Any?>(hwnd), WinNT.HRESULT::class.java) as WinNT.HRESULT

        fun SetOptions(fos: Int): WinNT.HRESULT =
            _invokeNativeObject(9, arrayOf(fos), WinNT.HRESULT::class.java) as WinNT.HRESULT

        fun SetTitle(pszTitle: String): WinNT.HRESULT =
            _invokeNativeObject(17, arrayOf(WString(pszTitle)), WinNT.HRESULT::class.java) as WinNT.HRESULT

        fun GetResult(ppsi: PointerByReference): WinNT.HRESULT =
            _invokeNativeObject(20, arrayOf(ppsi), WinNT.HRESULT::class.java) as WinNT.HRESULT
    }

    /** IShellItem: IUnknown(0-2) -> BindToHandler(3) -> GetParent(4) -> GetDisplayName(5) */
    private class ShellItem(ptr: Pointer) : Unknown(ptr) {
        fun GetDisplayName(sigdnName: Int, ppszName: PointerByReference): WinNT.HRESULT =
            _invokeNativeObject(5, arrayOf(sigdnName, ppszName), WinNT.HRESULT::class.java) as WinNT.HRESULT
    }

    private fun createDialog(): FileOpenDialog? {
        val pbr = PointerByReference()
        val hr = Ole32.INSTANCE.CoCreateInstance(
            CLSID_FileOpenDialog, null, CLSCTX_ALL, IID_IFileOpenDialog, pbr
        )
        if (hr != WinNT.S_OK || pbr.value == null) return null
        return FileOpenDialog(pbr.value)
    }

    /** 初始化当前线程的 COM（STA 模式），已初始化则忽略。 */
    private fun ensureComInitialized() {
        try {
            val hr = Ole32.INSTANCE.CoInitializeEx(Pointer.NULL, 0x2) // COINIT_APARTMENTTHREADED
            if (hr != WinNT.S_OK && hr != RPC_E_CHANGED_MODE) {
                Ole32.INSTANCE.CoInitializeEx(Pointer.NULL, 0x0) // COINIT_MULTITHREADED
            }
        } catch (_: Throwable) {
        }
    }

    /**
     * 显示现代 Windows 打开文件对话框。
     * @param title 对话框标题
     * @param pickFolders true=选择文件夹，false=选择文件
     * @return 选中的路径，取消则返回 null
     */
    fun showOpenDialog(title: String, pickFolders: Boolean): String? {
        ensureComInitialized()
        var dialog: FileOpenDialog? = null
        try {
            dialog = createDialog() ?: return null

            var options = FOS_PATHMUSTEXIST
            if (pickFolders) {
                options = options or FOS_PICKFOLDERS
            } else {
                options = options or FOS_FILEMUSTEXIST
            }
            dialog.SetOptions(options)
            dialog.SetTitle(title)

            val hr = dialog.Show(null)
            if (hr != WinNT.S_OK) return null // 用户取消或出错

            val ppsi = PointerByReference()
            if (dialog.GetResult(ppsi) != WinNT.S_OK) return null

            val shellItem = ShellItem(ppsi.value)
            try {
                val ppszName = PointerByReference()
                if (shellItem.GetDisplayName(SIGDN_FILESYSPATH, ppszName) != WinNT.S_OK) return null
                val pathPtr = ppszName.value ?: return null
                val path = pathPtr.getWideString(0)
                Ole32.INSTANCE.CoTaskMemFree(pathPtr)
                return path
            } finally {
                shellItem.Release()
            }
        } catch (_: Throwable) {
            return null
        } finally {
            dialog?.Release()
        }
    }
}
