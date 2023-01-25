class label:
    def __init__(self, screen, text, x, y, color, font):
        self.text = text
        self.y = y
        self.x = x
        self.color = color
        self.font = font
        self.screen = screen
        self.draw()
        
    def draw(self):
        self.screen.draw_string(self.text, self.x, self.y, self.color, self.font)
        self.screen.show()
        
    def set_text(self, text):
        data = self.screen.read_char(text[0], self.font)
        width = data[0]
        height = data[1]
        self.screen.draw_rect(self.x, self.y,
                         (len(self.text)+1)*width, height, self.screen.screen_color, True)
        self.text = text
        self.draw()
        
        
        
        
        