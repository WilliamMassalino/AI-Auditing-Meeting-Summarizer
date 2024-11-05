from frontend.app import create_gradio_interface

if __name__ == "__main__":
    iface = create_gradio_interface()
    iface.launch(debug=True)