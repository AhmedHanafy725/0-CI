<template>
  <div class="container">
    <h1 class="text-center text-light">ZeroCi Configuration</h1>

    <v-stepper v-model="currentStep" vertical dark non-linear>
      <v-stepper-step
        :editable="importStep >= 1"
        edit-icon="$vuetify.icons.complete"
        :complete="importStep > 1"
        step="1"
      >Version Control System</v-stepper-step>

      <v-stepper-content step="1">
        <form ref="form" @submit.prevent="vcsSubmit" lazy-validation>
          <div class="my-1" :class="{ 'form-group--error': $v.domain.$error }">
            <label class="text-white">Domain:</label>
            <input
              v-model.trim="$v.domain.$model"
              class="form-control"
              placeholder="Domain"
              required
            />
            <div class="error--text mb-2" v-if="!$v.domain.required">Domain is required</div>
            <p class="error--text mb-2" v-if="!$v.domain.url">Invalid Domain.</p>
          </div>

          <div class="my-1" :class="{ 'form-group--error': $v.vcs_host.$error }">
            <label class="text-white">Version Control System Host:</label>
            <input
              v-model.trim="$v.vcs_host.$model"
              class="form-control"
              placeholder="VCS Host"
              required
            />
            <div class="error--text mb-2" v-if="!$v.vcs_host.required">VCS Host is required</div>
            <p
              class="error--text mb-2"
              v-if="!$v.vcs_host.url"
            >Version Control System Host must contain http or https.</p>
          </div>

          <div class="my-1" :class="{ 'form-group--error': $v.vcs_token.$error }">
            <label class="text-white">Version Control System Token:</label>

            <input
              type="password"
              v-model.trim="$v.vcs_token.$model"
              class="form-control"
              placeholder="VCS Token"
              required
            />
            <div
              class="error--text mb-2"
              v-if="!$v.vcs_token.required"
            >Version Control System Token is required</div>
          </div>

          <button
            class="btn btn-primary btn-sm my-3"
            type="submit"
            :disabled="submitStatus === 'PENDING'"
          >Next Step</button>
          <button type="button" class="btn btn-secondary btn-sm" disabled>Back</button>

          <p class="typo__p success--text d-inline" v-if="submitStatus === 'OK'">{{submitMsg}}</p>
          <p class="typo__p error--text d-inline" v-if="submitStatus === 'ERROR'">{{submitMsg}}</p>
          <p class="typo__p warning--text d-inline" v-if="submitStatus === 'PENDING'">Sending...</p>
        </form>
      </v-stepper-content>

      <v-stepper-step
        :editable="importStep >= 2"
        edit-icon="$vuetify.icons.complete"
        :complete="importStep > 2"
        step="2"
        class="text-white"
      >Repositories</v-stepper-step>

      <v-stepper-content step="2">
        <form ref="form1" class="my-5" @submit.prevent="repoConfig" lazy-validation>
          <div class="my-1">
            <label class="text-white">Username:</label>
            <input
              v-model.trim="$v.username.$model"
              @blur="getReposWzUser"
              class="form-control"
              placeholder="Username"
            />
          </div>

          <div class="my-1">
            <label class="text-white">Organizations:</label>
            <input
              v-model.trim="$v.orgs.$model"
              @blur="getRepos"
              class="form-control"
              placeholder="Organizations"
            />
          </div>
          <v-combobox
            :class="{ 'form-group--error': $v.selectedRepos.$error }"
            v-model="selectedRepos"
            :items="allItems"
            label="Select Repos:"
            multiple
            chips
            :loading="loading"
            :disabled="selectedRepos > 0"
          ></v-combobox>
          <div class="error--text mb-2" v-if="!$v.selectedRepos.required">Repositories is required</div>

          <button
            class="btn btn-primary btn-sm my-3"
            type="submit"
            :disabled="submitStatus === 'PENDING'"
          >Next Step</button>
          <button type="button" class="btn btn-secondary btn-sm" @click="currentStep = 1">Back</button>

          <p class="typo__p success--text d-inline" v-if="submitStatus === 'OK'">{{submitMsg}}</p>
          <p class="typo__p error--text d-inline" v-if="submitStatus === 'ERROR'">{{submitMsg}}</p>
          <p class="typo__p warning--text d-inline" v-if="submitStatus === 'PENDING'">Sending...</p>
        </form>
      </v-stepper-content>

      <v-stepper-step
        :editable="importStep >= 3"
        edit-icon="$vuetify.icons.complete"
        :complete="importStep > 3"
        step="3"
        class="text-white"
      >Telegram</v-stepper-step>

      <v-stepper-content step="3">
        <form ref="form2" class="my-5" @submit.prevent="telegramConfig" lazy-validation>
          <div class="my-1" :class="{ 'form-group--error': $v.chat_id.$error }">
            <label class="text-white">Group Telegram ID:</label>
            <input
              v-model.trim="$v.chat_id.$model"
              class="form-control"
              placeholder="@Telegram ID"
              required
            />
            <div class="error--text mb-2" v-if="!$v.chat_id.required">Group Telegram ID is required</div>
          </div>

          <div class="my-1" :class="{ 'form-group--error': $v.bot_token.$error }">
            <label class="text-white">Telegram Token:</label>
            <input
              type="password"
              v-model.trim="$v.bot_token.$model"
              class="form-control"
              placeholder="Telegram Token"
              required
            />
            <div class="error--text mb-2" v-if="!$v.bot_token.required">Telegram Token is required</div>
          </div>
          <button
            class="btn btn-primary btn-sm my-3"
            type="submit"
            :disabled="submitStatus === 'PENDING'"
          >Next Step</button>
          <button type="button" class="btn btn-secondary btn-sm" @click="currentStep = 2">Back</button>
          <p class="typo__p success--text d-inline" v-if="submitStatus === 'OK'">{{submitMsg}}</p>
          <p class="typo__p error--text d-inline" v-if="submitStatus === 'ERROR'">{{submitMsg}}</p>
          <p class="typo__p warning--text d-inline" v-if="submitStatus === 'PENDING'">Sending...</p>
        </form>
      </v-stepper-content>

      <v-stepper-step
        :editable="importStep >= 4"
        edit-icon="$vuetify.icons.complete"
        :complete="importStep > 4"
        step="4"
        class="text-white"
      >Apply</v-stepper-step>

      <v-stepper-content step="4">
        <button class="btn btn-primary btn-sm my-3" @click="applyConfig()">Apply</button>
        <button type="button" class="btn btn-secondary btn-sm" @click="currentStep = 3">Back</button>
      </v-stepper-content>
    </v-stepper>
  </div>
</template>

<script>
import EventService from "../services/EventService";
import { required, url } from "vuelidate/lib/validators";

export default {
  name: "InitialConfig",
  data() {
    return {
      valid: true,
      domain: "",
      bot_token: "",
      chat_id: "",
      vcs_host: "",
      vcs_token: "",
      username: "",
      orgs: "",
      disabled: true,
      loading: false,
      currentStep: 1,
      importStep: 1,
      submitStatus: null,
      submitMsg: "",
      selectedRepos: [],
      items: [],
      userRepos: [],
      orgRepos: []
    };
  },
  validations: {
    domain: {
      required,
      url
    },
    vcs_host: {
      required,
      url
    },
    vcs_token: {
      required
    },
    username: {
      required
    },
    orgs: {
      required
    },
    repos: {
      required
    },
    selectedRepos: {
      required
    },
    chat_id: {
      required
    },
    bot_token: {
      required
    }
  },
  methods: {
    getVCS() {
      EventService.getVcs()
        .then(response => {
          this.domain = response.data.domain;
          this.vcs_host = response.data.vcs_host;
          this.vcs_token = response.data.vcs_token;
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    vcsSubmit() {
      this.submitStatus = "PENDING";
      EventService.postVCS(this.domain, this.vcs_host, this.vcs_token)
        .then(response => {
          this.submitStatus = "OK";
          this.submitMsg = response.data;
          setTimeout(() => {
            this.currentStep = 2;
            this.importStep = Math.max(this.importStep, 2);
            this.submitMsg = null;
          }, 1000);
        })
        .catch(error => {
          this.submitStatus = "ERROR";
          this.submitMsg = error.response.data;
          console.log("Error! Could not reach the API. " + error);
        });
    },
    currentRepos() {
      EventService.getCurrentRepos()
        .then(response => {
          this.selectedRepos = response.data;
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    getReposWzUser() {
      this.loading = true;
      EventService.getReposWzUsername(this.username)
        .then(response => {
          this.loading = false;
          if (isArray(response.data)) {
            this.disabled = false;
            this.userRepos = response.data;
          } else {
            this.submitStatus = "ERROR";
            this.submitMsg = response.data;
          }
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    getRepos() {
      this.loading = true;
      EventService.getRepos(this.newOrgs)
        .then(response => {
          this.loading = false;
          if (isArray(response)) {
            this.disabled = false;
            this.orgRepos = [].concat.apply([], response);
          } else {
            this.submitStatus = "ERROR";
            this.submitMsg = response.data;
          }
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    repoConfig() {
      this.submitStatus = "PENDING";
      EventService.sendRepos(this.selectedRepos)
        .then(response => {
          this.submitStatus = "OK";
          this.submitMsg = response.data;
          setTimeout(() => {
            this.currentStep = 3;
            this.importStep = Math.max(this.importStep, 3);
            this.submitMsg = null;
          }, 1000);
        })
        .catch(error => {
          this.submitStatus = "ERROR";
          this.submitMsg = error.response.data;
          console.log("Error! Could not reach the API. " + error);
        });
    },
    getTelegramConfig() {
      EventService.getTelegram()
        .then(response => {
          this.chat_id = response.data.chat_id;
          this.bot_token = response.data.bot_token;
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    telegramConfig() {
      EventService.setTelegramConfig(this.chat_id, this.bot_token)
        .then(response => {
          this.submitStatus = "OK";
          this.submitMsg = response.data;
          setTimeout(() => {
            this.currentStep = 4;
            this.importStep = Math.max(this.importStep, 4);
            this.submitMsg = null;
          }, 1000);
        })
        .catch(error => {
          this.submitStatus = "ERROR";
          this.submitMsg = error.response.data;
          console.log("Error! Could not reach the API. " + error);
        });
    },
    applyConfig() {
      EventService.applyConfig()
        .then(response => {
          this.$router.push("/");
        })
        .catch(error => {
          this.submitStatus = "ERROR";
          this.submitMsg = error.response.data;
          console.log("Error! Could not reach the API. " + error);
        });
    }
  },
  computed: {
    newOrgs() {
      return this.orgs.split(/[ ,]+/);
    },
    allItems() {
      this.items = this.userRepos.concat(this.orgRepos);
      return this.items;
    }
  },
  created() {
    this.getVCS();
    this.currentRepos();
    this.getTelegramConfig();
  }
};
</script>

<style scoped>
.v-stepper {
  box-shadow: none;
}
.theme--dark.v-stepper {
  background: rgba(27, 17, 44, 0.25);
}

h1 {
  margin-top: 3rem;
  margin-bottom: 3rem;
}
.v-stepper__step__step .primary {
  background-color: #2e40d4 !important;
  border-color: #2e40d4 !important;
}

.config .form-control {
  height: 46px;
  border: none;
  padding-left: 1.5rem;
  padding-right: 1.5rem;
  border-radius: 46px;
  margin-top: 0.5rem;
  background: rgba(255, 255, 255, 0.015);
  color: #a7abc3;
}

.theme--dark.v-application {
  font-size: 1rem;
  font-weight: 400;
  color: #a7abc3 !important;
}

label {
  margin-top: 0.5rem;
}
</style>
