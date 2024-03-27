package main

import (
	"log"
	"os"
	"os/exec"
	"time"

	"github.com/gofiber/fiber/v2"
)

func main() {
	app := fiber.New()

	app.Get("/", func(c *fiber.Ctx) error {
		return c.Render("index.html", fiber.Map{})
	})

	app.Post("/submit", func(c *fiber.Ctx) error {
		// Get the file from the form.
		file, err := c.FormFile("file")
		if err != nil {
			return err
		}

		// Get the text from the form.
		text := c.FormValue("text")

		// Save the file.
		if err := c.SaveFile(file, "./"+file.Filename); err != nil {
			return err
		}

		// Execute the Python script.
		cmd := exec.Command("python3", "main.py", "-f", file.Filename, "-p", text, "-g", "True")
		_, err = cmd.Output()
		if err != nil {
			log.Fatal(err)
			return err
		}

		os.Remove(file.Filename)

		timer := time.NewTimer(5 * time.Second)
		go func() {
			<-timer.C
			os.Remove(file.Filename + ".html")
		}()

		// Send the HTML response.
		return c.Render(file.Filename+".html", fiber.Map{})
	})

	log.Fatal(app.Listen(":8082"))
}
