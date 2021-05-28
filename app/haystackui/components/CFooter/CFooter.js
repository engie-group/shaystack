const template = `
  <v-footer :padless=true absolute>
    <v-card flat tile width="100%" class="grey lighten-3 text-center">
      <v-card-text style="display:flex">
        <div class="footer__help">
          <h3>How to join us</h3>
          <br />
          <a href="https://github.com/engie-group/shaystack" class="footer__help-links">
            Github Project
          </a>
          <a href="mailto:franck.SEUTIN@engie.com" class="footer__help-links">
            Contact
          </a>
        </div>
      </v-card-text>
      <v-divider></v-divider>
      <v-card-text class="grey--text">
        <strong>Haystack Version 1.0</strong>
      </v-card-text>
    </v-card>
  </v-footer>
`

export default {
  template,
  name: 'CFooter'
}
