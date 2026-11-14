const e=globalThis,t=e.ShadowRoot&&(void 0===e.ShadyCSS||e.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,i=Symbol(),r=new WeakMap;let s=class{constructor(e,t,r){if(this._$cssResult$=!0,r!==i)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o;const i=this.t;if(t&&void 0===e){const t=void 0!==i&&1===i.length;t&&(e=r.get(i)),void 0===e&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),t&&r.set(i,e))}return e}toString(){return this.cssText}};const a=(e,...t)=>{const r=1===e.length?e[0]:t.reduce((t,i,r)=>t+(e=>{if(!0===e._$cssResult$)return e.cssText;if("number"==typeof e)return e;throw Error("Value passed to 'css' function must be a 'css' function result: "+e+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+e[r+1],e[0]);return new s(r,e,i)},n=t?e=>e:e=>e instanceof CSSStyleSheet?(e=>{let t="";for(const i of e.cssRules)t+=i.cssText;return(e=>new s("string"==typeof e?e:e+"",void 0,i))(t)})(e):e,{is:o,defineProperty:l,getOwnPropertyDescriptor:d,getOwnPropertyNames:c,getOwnPropertySymbols:h,getPrototypeOf:p}=Object,u=globalThis,_=u.trustedTypes,m=_?_.emptyScript:"",g=u.reactiveElementPolyfillSupport,v=(e,t)=>e,$={toAttribute(e,t){switch(t){case Boolean:e=e?m:null;break;case Object:case Array:e=null==e?e:JSON.stringify(e)}return e},fromAttribute(e,t){let i=e;switch(t){case Boolean:i=null!==e;break;case Number:i=null===e?null:Number(e);break;case Object:case Array:try{i=JSON.parse(e)}catch(e){i=null}}return i}},y=(e,t)=>!o(e,t),f={attribute:!0,type:String,converter:$,reflect:!1,useDefault:!1,hasChanged:y};Symbol.metadata??=Symbol("metadata"),u.litPropertyMetadata??=new WeakMap;let b=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=f){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){const i=Symbol(),r=this.getPropertyDescriptor(e,i,t);void 0!==r&&l(this.prototype,e,r)}}static getPropertyDescriptor(e,t,i){const{get:r,set:s}=d(this.prototype,e)??{get(){return this[t]},set(e){this[t]=e}};return{get:r,set(t){const a=r?.call(this);s?.call(this,t),this.requestUpdate(e,a,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??f}static _$Ei(){if(this.hasOwnProperty(v("elementProperties")))return;const e=p(this);e.finalize(),void 0!==e.l&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(v("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(v("properties"))){const e=this.properties,t=[...c(e),...h(e)];for(const i of t)this.createProperty(i,e[i])}const e=this[Symbol.metadata];if(null!==e){const t=litPropertyMetadata.get(e);if(void 0!==t)for(const[e,i]of t)this.elementProperties.set(e,i)}this._$Eh=new Map;for(const[e,t]of this.elementProperties){const i=this._$Eu(e,t);void 0!==i&&this._$Eh.set(i,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){const t=[];if(Array.isArray(e)){const i=new Set(e.flat(1/0).reverse());for(const e of i)t.unshift(n(e))}else void 0!==e&&t.push(n(e));return t}static _$Eu(e,t){const i=t.attribute;return!1===i?void 0:"string"==typeof i?i:"string"==typeof e?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),void 0!==this.renderRoot&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){const e=new Map,t=this.constructor.elementProperties;for(const i of t.keys())this.hasOwnProperty(i)&&(e.set(i,this[i]),delete this[i]);e.size>0&&(this._$Ep=e)}createRenderRoot(){const i=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((i,r)=>{if(t)i.adoptedStyleSheets=r.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(const t of r){const r=document.createElement("style"),s=e.litNonce;void 0!==s&&r.setAttribute("nonce",s),r.textContent=t.cssText,i.appendChild(r)}})(i,this.constructor.elementStyles),i}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,i){this._$AK(e,i)}_$ET(e,t){const i=this.constructor.elementProperties.get(e),r=this.constructor._$Eu(e,i);if(void 0!==r&&!0===i.reflect){const s=(void 0!==i.converter?.toAttribute?i.converter:$).toAttribute(t,i.type);this._$Em=e,null==s?this.removeAttribute(r):this.setAttribute(r,s),this._$Em=null}}_$AK(e,t){const i=this.constructor,r=i._$Eh.get(e);if(void 0!==r&&this._$Em!==r){const e=i.getPropertyOptions(r),s="function"==typeof e.converter?{fromAttribute:e.converter}:void 0!==e.converter?.fromAttribute?e.converter:$;this._$Em=r;const a=s.fromAttribute(t,e.type);this[r]=a??this._$Ej?.get(r)??a,this._$Em=null}}requestUpdate(e,t,i,r=!1,s){if(void 0!==e){const a=this.constructor;if(!1===r&&(s=this[e]),i??=a.getPropertyOptions(e),!((i.hasChanged??y)(s,t)||i.useDefault&&i.reflect&&s===this._$Ej?.get(e)&&!this.hasAttribute(a._$Eu(e,i))))return;this.C(e,t,i)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(e,t,{useDefault:i,reflect:r,wrapped:s},a){i&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,a??t??this[e]),!0!==s||void 0!==a)||(this._$AL.has(e)||(this.hasUpdated||i||(t=void 0),this._$AL.set(e,t)),!0===r&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}const e=this.scheduleUpdate();return null!=e&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[e,t]of this._$Ep)this[e]=t;this._$Ep=void 0}const e=this.constructor.elementProperties;if(e.size>0)for(const[t,i]of e){const{wrapped:e}=i,r=this[t];!0!==e||this._$AL.has(t)||void 0===r||this.C(t,void 0,i,r)}}let e=!1;const t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(e=>e.hostUpdate?.()),this.update(t)):this._$EM()}catch(t){throw e=!1,this._$EM(),t}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(e){}firstUpdated(e){}};b.elementStyles=[],b.shadowRootOptions={mode:"open"},b[v("elementProperties")]=new Map,b[v("finalized")]=new Map,g?.({ReactiveElement:b}),(u.reactiveElementVersions??=[]).push("2.1.2");const x=globalThis,w=e=>e,k=x.trustedTypes,A=k?k.createPolicy("lit-html",{createHTML:e=>e}):void 0,E="$lit$",C=`lit$${Math.random().toFixed(9).slice(2)}$`,S="?"+C,P=`<${S}>`,M=document,N=()=>M.createComment(""),U=e=>null===e||"object"!=typeof e&&"function"!=typeof e,I=Array.isArray,O="[ \t\n\f\r]",H=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,T=/-->/g,D=/>/g,R=RegExp(`>|${O}(?:([^\\s"'>=/]+)(${O}*=${O}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),z=/'/g,W=/"/g,j=/^(?:script|style|textarea|title)$/i,L=e=>(t,...i)=>({_$litType$:e,strings:t,values:i}),q=L(1),B=L(2),F=Symbol.for("lit-noChange"),V=Symbol.for("lit-nothing"),K=new WeakMap,G=M.createTreeWalker(M,129);function Z(e,t){if(!I(e)||!e.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==A?A.createHTML(t):t}const J=(e,t)=>{const i=e.length-1,r=[];let s,a=2===t?"<svg>":3===t?"<math>":"",n=H;for(let t=0;t<i;t++){const i=e[t];let o,l,d=-1,c=0;for(;c<i.length&&(n.lastIndex=c,l=n.exec(i),null!==l);)c=n.lastIndex,n===H?"!--"===l[1]?n=T:void 0!==l[1]?n=D:void 0!==l[2]?(j.test(l[2])&&(s=RegExp("</"+l[2],"g")),n=R):void 0!==l[3]&&(n=R):n===R?">"===l[0]?(n=s??H,d=-1):void 0===l[1]?d=-2:(d=n.lastIndex-l[2].length,o=l[1],n=void 0===l[3]?R:'"'===l[3]?W:z):n===W||n===z?n=R:n===T||n===D?n=H:(n=R,s=void 0);const h=n===R&&e[t+1].startsWith("/>")?" ":"";a+=n===H?i+P:d>=0?(r.push(o),i.slice(0,d)+E+i.slice(d)+C+h):i+C+(-2===d?t:h)}return[Z(e,a+(e[i]||"<?>")+(2===t?"</svg>":3===t?"</math>":"")),r]};class Y{constructor({strings:e,_$litType$:t},i){let r;this.parts=[];let s=0,a=0;const n=e.length-1,o=this.parts,[l,d]=J(e,t);if(this.el=Y.createElement(l,i),G.currentNode=this.el.content,2===t||3===t){const e=this.el.content.firstChild;e.replaceWith(...e.childNodes)}for(;null!==(r=G.nextNode())&&o.length<n;){if(1===r.nodeType){if(r.hasAttributes())for(const e of r.getAttributeNames())if(e.endsWith(E)){const t=d[a++],i=r.getAttribute(e).split(C),n=/([.?@])?(.*)/.exec(t);o.push({type:1,index:s,name:n[2],strings:i,ctor:"."===n[1]?ie:"?"===n[1]?re:"@"===n[1]?se:te}),r.removeAttribute(e)}else e.startsWith(C)&&(o.push({type:6,index:s}),r.removeAttribute(e));if(j.test(r.tagName)){const e=r.textContent.split(C),t=e.length-1;if(t>0){r.textContent=k?k.emptyScript:"";for(let i=0;i<t;i++)r.append(e[i],N()),G.nextNode(),o.push({type:2,index:++s});r.append(e[t],N())}}}else if(8===r.nodeType)if(r.data===S)o.push({type:2,index:s});else{let e=-1;for(;-1!==(e=r.data.indexOf(C,e+1));)o.push({type:7,index:s}),e+=C.length-1}s++}}static createElement(e,t){const i=M.createElement("template");return i.innerHTML=e,i}}function Q(e,t,i=e,r){if(t===F)return t;let s=void 0!==r?i._$Co?.[r]:i._$Cl;const a=U(t)?void 0:t._$litDirective$;return s?.constructor!==a&&(s?._$AO?.(!1),void 0===a?s=void 0:(s=new a(e),s._$AT(e,i,r)),void 0!==r?(i._$Co??=[])[r]=s:i._$Cl=s),void 0!==s&&(t=Q(e,s._$AS(e,t.values),s,r)),t}class X{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){const{el:{content:t},parts:i}=this._$AD,r=(e?.creationScope??M).importNode(t,!0);G.currentNode=r;let s=G.nextNode(),a=0,n=0,o=i[0];for(;void 0!==o;){if(a===o.index){let t;2===o.type?t=new ee(s,s.nextSibling,this,e):1===o.type?t=new o.ctor(s,o.name,o.strings,this,e):6===o.type&&(t=new ae(s,this,e)),this._$AV.push(t),o=i[++n]}a!==o?.index&&(s=G.nextNode(),a++)}return G.currentNode=M,r}p(e){let t=0;for(const i of this._$AV)void 0!==i&&(void 0!==i.strings?(i._$AI(e,i,t),t+=i.strings.length-2):i._$AI(e[t])),t++}}class ee{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,i,r){this.type=2,this._$AH=V,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=i,this.options=r,this._$Cv=r?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode;const t=this._$AM;return void 0!==t&&11===e?.nodeType&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=Q(this,e,t),U(e)?e===V||null==e||""===e?(this._$AH!==V&&this._$AR(),this._$AH=V):e!==this._$AH&&e!==F&&this._(e):void 0!==e._$litType$?this.$(e):void 0!==e.nodeType?this.T(e):(e=>I(e)||"function"==typeof e?.[Symbol.iterator])(e)?this.k(e):this._(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==V&&U(this._$AH)?this._$AA.nextSibling.data=e:this.T(M.createTextNode(e)),this._$AH=e}$(e){const{values:t,_$litType$:i}=e,r="number"==typeof i?this._$AC(e):(void 0===i.el&&(i.el=Y.createElement(Z(i.h,i.h[0]),this.options)),i);if(this._$AH?._$AD===r)this._$AH.p(t);else{const e=new X(r,this),i=e.u(this.options);e.p(t),this.T(i),this._$AH=e}}_$AC(e){let t=K.get(e.strings);return void 0===t&&K.set(e.strings,t=new Y(e)),t}k(e){I(this._$AH)||(this._$AH=[],this._$AR());const t=this._$AH;let i,r=0;for(const s of e)r===t.length?t.push(i=new ee(this.O(N()),this.O(N()),this,this.options)):i=t[r],i._$AI(s),r++;r<t.length&&(this._$AR(i&&i._$AB.nextSibling,r),t.length=r)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){const t=w(e).nextSibling;w(e).remove(),e=t}}setConnected(e){void 0===this._$AM&&(this._$Cv=e,this._$AP?.(e))}}class te{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,i,r,s){this.type=1,this._$AH=V,this._$AN=void 0,this.element=e,this.name=t,this._$AM=r,this.options=s,i.length>2||""!==i[0]||""!==i[1]?(this._$AH=Array(i.length-1).fill(new String),this.strings=i):this._$AH=V}_$AI(e,t=this,i,r){const s=this.strings;let a=!1;if(void 0===s)e=Q(this,e,t,0),a=!U(e)||e!==this._$AH&&e!==F,a&&(this._$AH=e);else{const r=e;let n,o;for(e=s[0],n=0;n<s.length-1;n++)o=Q(this,r[i+n],t,n),o===F&&(o=this._$AH[n]),a||=!U(o)||o!==this._$AH[n],o===V?e=V:e!==V&&(e+=(o??"")+s[n+1]),this._$AH[n]=o}a&&!r&&this.j(e)}j(e){e===V?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??"")}}class ie extends te{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===V?void 0:e}}class re extends te{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==V)}}class se extends te{constructor(e,t,i,r,s){super(e,t,i,r,s),this.type=5}_$AI(e,t=this){if((e=Q(this,e,t,0)??V)===F)return;const i=this._$AH,r=e===V&&i!==V||e.capture!==i.capture||e.once!==i.once||e.passive!==i.passive,s=e!==V&&(i===V||r);r&&this.element.removeEventListener(this.name,this,i),s&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}}class ae{constructor(e,t,i){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=i}get _$AU(){return this._$AM._$AU}_$AI(e){Q(this,e)}}const ne=x.litHtmlPolyfillSupport;ne?.(Y,ee),(x.litHtmlVersions??=[]).push("3.3.3");const oe=globalThis;class le extends b{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){const t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=((e,t,i)=>{const r=i?.renderBefore??t;let s=r._$litPart$;if(void 0===s){const e=i?.renderBefore??null;r._$litPart$=s=new ee(t.insertBefore(N(),e),e,void 0,i??{})}return s._$AI(e),s})(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return F}}le._$litElement$=!0,le.finalized=!0,oe.litElementHydrateSupport?.({LitElement:le});const de=oe.litElementPolyfillSupport;de?.({LitElement:le}),(oe.litElementVersions??=[]).push("4.2.2");const ce="—";function he(e,t,i,r){const s={minimumFractionDigits:i,maximumFractionDigits:r};let a;try{a=new Intl.NumberFormat(e,s)}catch(e){if(!(e instanceof RangeError))throw e;a=new Intl.NumberFormat("en",s)}return a.format(t).replace(/[  ]/g," ")}function pe(e){const t=/^(\d{4})-(\d{2})-(\d{2})/.exec(e);return t?`${t[3]}/${t[2]}/${t[1]}`:e}function ue(e,t){const i=pe(e),r=pe(t);return e.slice(0,4)===t.slice(0,4)?`${i.slice(0,5)} – ${r}`:`${i} – ${r}`}function _e(e,t){return null===t?ce:`${he(e,t,0,2)} kWh`}function me(e,t){return null===t?ce:`${he(e,t,2,2)} €`}function ge(e,t){return null===t?ce:`${he(e,t,4,4)} €/kWh`}function ve(e,t){return null===t?ce:`${he(e,t,1,1)} %`}function $e(e,t,i){if(null===t)return ce;const r="kwh"===i?"kWh":"€",s="kwh"===i?[0,2]:[2,2],a=he(e,Math.abs(t),...s);return`${0===Number(Math.abs(t).toFixed(s[1]))?"":t<0?"−":"+"}${a} ${r}`}function ye(e,t){return null===t?ce:`${he(e,t,0,2)} m³`}function fe(e,t){return null===t?ce:`${he(e,t,0,2)} %`}const be={es:{pill_estimated:"estimada",pill_unreadable:"no se pudo leer",pill_no_invoice:"sin factura",gap_hint:"No hay factura guardada de este periodo; puede ser un correo que no se pudo leer.",tab_electricity:"Luz",tab_gas:"Gas",col_period:"Periodo",col_kwh_invoice:"kWh factura",col_kwh_edata:"kWh Datadis",col_delta_kwh:"Δ kWh",col_amount:"Importe",col_delta_eur:"Δ €",col_kwh:"kWh",col_m3:"m³",col_price_kwh:"€/kWh",detail_power_energy:"Potencia + energía: factura {invoice} / e-data {edata}",detail_delta_pct:"Δ {pct}",detail_group:"Comparada junto con: {numbers}",detail_in_group_of:"Regularizada en la factura {number}",detail_vat:"IVA {rate} sobre {base}: {amount}",detail_energy_price:"Precio de la energía: {price}",detail_meter_current:"Lectura actual ({kind}, {date})",detail_meter_previous:"Lectura anterior ({kind}, {date})",meter_title:"Última lectura facturada",meter_since_previous:"{diff} desde la anterior ({value}, {kind}, {date})",meter_real:"real",meter_estimated:"estimada",meter_p1:"P1 (punta)",meter_p2:"P2 (llano)",meter_p3:"P3 (valle)",detail_period_row:"{period}: factura {invoice} / Datadis {edata}",row_covers:"abarca {n} facturas",detail_own_kwh:"Esta factura: {kwh}",detail_group_heading:"Comparación del grupo ({n} facturas)",card_title:"Facturas",loading:"Cargando…",empty:"Todavía no hay facturas",error:"No se pudieron cargar las facturas",card_description:"Facturas de CurEnergía comparadas con los datos de Datadis",chart_title:"kWh por factura",chart_empty:"Sin datos para el gráfico",chart_invoice:"Factura",chart_datadis:"Datadis",panel_title:"Facturas",panel_menu:"Menú",panel_billed_12m:"Facturado en 12 meses",panel_kwh_delta:"kWh factura vs Datadis",panel_estimated_count:"Lecturas estimadas",panel_unreadable:"Correos con factura que no se pudo leer: {n}",panel_unsupported:"Correos con factura no soportada (rectificativa o abono) o demasiado grande (más de 15 MB): {n}",panel_mail_error:"No se pudo leer el correo; se muestran las facturas guardadas",editor_title:"Título",editor_supply:"Pestaña inicial",editor_max_invoices:"Número máximo de facturas",editor_entry_id:"Cuenta de correo (opcional)",editor_columns_electricity:"Columnas de luz (ninguna marcada = todas)",editor_columns_gas:"Columnas de gas (ninguna marcada = todas)"},en:{pill_estimated:"estimated",pill_unreadable:"could not be read",pill_no_invoice:"no invoice",gap_hint:"No invoice stored for this period; it may be an e-mail that could not be read.",tab_electricity:"Electricity",tab_gas:"Gas",col_period:"Period",col_kwh_invoice:"Invoice kWh",col_kwh_edata:"Datadis kWh",col_delta_kwh:"Δ kWh",col_amount:"Amount",col_delta_eur:"Δ €",col_kwh:"kWh",col_m3:"m³",col_price_kwh:"€/kWh",detail_power_energy:"Power + energy: invoice {invoice} / e-data {edata}",detail_delta_pct:"Δ {pct}",detail_group:"Compared together with: {numbers}",detail_in_group_of:"Settled by invoice {number}",detail_vat:"VAT {rate} on {base}: {amount}",detail_energy_price:"Energy price: {price}",detail_meter_current:"Current reading ({kind}, {date})",detail_meter_previous:"Previous reading ({kind}, {date})",meter_title:"Latest billed reading",meter_since_previous:"{diff} since the previous one ({value}, {kind}, {date})",meter_real:"measured",meter_estimated:"estimated",meter_p1:"P1 (peak)",meter_p2:"P2 (standard)",meter_p3:"P3 (off-peak)",detail_period_row:"{period}: invoice {invoice} / Datadis {edata}",row_covers:"covers {n} invoices",detail_own_kwh:"This invoice: {kwh}",detail_group_heading:"Group comparison ({n} invoices)",card_title:"Invoices",loading:"Loading…",empty:"No invoices yet",error:"Could not load the invoices",card_description:"CurEnergía invoices compared with Datadis data",chart_title:"kWh per invoice",chart_empty:"No data for the chart",chart_invoice:"Invoice",chart_datadis:"Datadis",panel_title:"Invoices",panel_menu:"Menu",panel_billed_12m:"Billed in 12 months",panel_kwh_delta:"Invoice kWh vs Datadis",panel_estimated_count:"Estimated readings",panel_unreadable:"E-mails with an invoice that could not be read: {n}",panel_unsupported:"E-mails with an invoice that is not supported (corrective or credit note) or too large (over 15 MB): {n}",panel_mail_error:"Could not read the mailbox; showing the saved invoices",editor_title:"Title",editor_supply:"Initial tab",editor_max_invoices:"Maximum number of invoices",editor_entry_id:"Mail account (optional)",editor_columns_electricity:"Electricity columns (none ticked = all)",editor_columns_gas:"Gas columns (none ticked = all)"}};function xe(e){return e.locale?.language||e.language||"en"}function we(e,t,i){return ke(xe(e),t,i)}function ke(e,t,i){const r=(e.toLowerCase().startsWith("es")?be.es:be.en)[t];return i?r.replace(/\{(\w+)\}/g,(e,t)=>t in i?String(i[t]):e):r}const Ae=[{supply:"electricity",label:"tab_electricity"},{supply:"gas",label:"tab_gas"}],Ee={electricity:[{id:"kwh_invoice",label:"col_kwh_invoice"},{id:"kwh_edata",label:"col_kwh_edata"},{id:"delta_kwh",label:"col_delta_kwh"},{id:"amount",label:"col_amount"},{id:"delta_eur",label:"col_delta_eur"},{id:"price_kwh",label:"col_price_kwh"}],gas:[{id:"kwh",label:"col_kwh"},{id:"m3",label:"col_m3"},{id:"amount",label:"col_amount"},{id:"price_kwh",label:"col_price_kwh"}]},Ce=[{key:"p1",name:"P1"},{key:"p2",name:"P2"},{key:"p3",name:"P3"}],Se=[{key:"p1",label:"meter_p1"},{key:"p2",label:"meter_p2"},{key:"p3",label:"meter_p3"}];function Pe(e,t){return t.period_end.localeCompare(e.period_end)||t.issue_date.localeCompare(e.issue_date)||t.number.localeCompare(e.number)}class Me extends le{constructor(){super(),this.contracts=[],this.supply="electricity",this._expanded=new Set}render(){const e=(this.contracts??[]).filter(e=>e.supply===this.supply);return q`
      <div class="tabs" role="tablist">
        ${Ae.map(({supply:e,label:t})=>q`
            <button
              class="tab"
              role="tab"
              type="button"
              aria-selected=${e===this.supply?"true":"false"}
              @click=${()=>this._selectSupply(e)}
            >
              ${we(this.hass,t)}
            </button>
          `)}
      </div>
      ${0===e.length?q`<div class="empty">${we(this.hass,"empty")}</div>`:e.map(t=>this._renderContract(t,e.length>1))}
    `}_renderContract(e,t){const i=[...e.invoices].sort(Pe),r=this.maxInvoices,s=r&&r>0?i.slice(0,r):i,a=["col_period",...this._visible(this.supply).map(e=>e.label)];return q`
      ${t?q`<h3 class="contract-name">${e.name}</h3>`:V}
      ${this._renderMeter((n=i,n.find(e=>e.meter&&"no_leida"!==e.status)?.meter??null))}
      <div class="scroll">
        <table>
          <thead>
            <tr>
              ${a.map(e=>q`<th>${we(this.hass,e)}</th>`)}
            </tr>
          </thead>
          <tbody>
            ${s.map((t,i)=>[this._renderRow(e,t,a.length),this._renderGap(t,s[i+1],a.length)])}
          </tbody>
        </table>
      </div>
    `;var n}_visible(e){const t=Ee[e],i=this.columns?.[e];return i&&0!==i.length?t.filter(e=>i.includes(e.id)):t}_renderGap(e,t,i){const r=t?function(e,t){const i=Date.parse(t.period_end),r=Date.parse(e.period_start);return Number.isNaN(i)||Number.isNaN(r)||r-i<=864e5?null:{start:t.period_end,end:e.period_start}}(e,t):null;return null===r?V:q`
      <tr class="gap">
        <td colspan=${i}>
          ${ue(r.start,r.end)}
          <span class="pill">${we(this.hass,"pill_no_invoice")}</span>
          <span class="gap-hint">${we(this.hass,"gap_hint")}</span>
        </td>
      </tr>
    `}_meterKind(e){return we(this.hass,e?"meter_estimated":"meter_real")}_renderMeter(e){if(!e)return V;const t=xe(this.hass),i=e.previous,r=q`<span class="pill">${this._meterKind(e.estimated)}</span>`;return q`
      <div class="meter">
        <div class="meter-note">${we(this.hass,"meter_title")}</div>
        ${null!==e.m3?q`<div class="meter-value">${ye(t,e.m3)} ${r}</div>
              <div class="meter-note">
                ${pe(e.read_on)}
                ${i&&null!==i.m3?q`·
                    ${we(this.hass,"meter_since_previous",{diff:ye(t,e.m3-i.m3),value:ye(t,i.m3),kind:this._meterKind(i.estimated),date:pe(i.read_on)})}`:V}
              </div>`:q`<div class="meter-note">${pe(e.read_on)} ${r}</div>
              <div class="meter-periods">
                ${Se.map(({key:i,label:r})=>q`<div>
                      <span class="meter-note">${we(this.hass,r)}</span>
                      <strong>${_e(t,e.periods?.[i]??null)}</strong>
                    </div>`)}
              </div>`}
      </div>
    `}_renderMeterDetail(e){const t=xe(this.hass),i=e.previous,r=we(this.hass,"detail_meter_current",{kind:this._meterKind(e.estimated),date:pe(e.read_on)});return null===e.m3?q`<div>${r}</div>
        <ul>
          ${Se.map(({key:i,label:r})=>q`<li>
                <span>${we(this.hass,r)}</span>
                <span>${_e(t,e.periods?.[i]??null)}</span>
              </li>`)}
        </ul>`:q`<ul>
      <li><span>${r}</span><span>${ye(t,e.m3)}</span></li>
      ${i?q`<li>
            <span>
              ${we(this.hass,"detail_meter_previous",{kind:this._meterKind(i.estimated),date:pe(i.read_on)})}
            </span>
            <span>${ye(t,i.m3)}</span>
          </li>`:V}
    </ul>`}_renderRow(e,t,i){const r=xe(this.hass),s=`${e.entry_id}|${e.contract}|${t.number}`,a=this._expanded.has(s),n=t.comparison?.group.length??0,o="color: var(--secondary-text-color)",l=null==t.comparison?.delta_kwh?o:`color: var(${function(e){switch(e){case"ok":return"--success-color";case"no_cuadra":return"--warning-color";case"no_leida":return"--error-color";default:return"--secondary-text-color"}}(t.status)})`,d=q`
      <td>
        <button class="toggle" type="button" aria-expanded=${a?"true":"false"}>
          ${ue(t.period_start,t.period_end)}
          ${t.estimated?q`<span class="pill">${we(this.hass,"pill_estimated")}</span>`:V}
          ${"no_leida"===t.status?q`<span class="pill error">${we(this.hass,"pill_unreadable")}</span>`:V}
          ${n>1?q`<span class="note">${we(this.hass,"row_covers",{n:n})}</span>`:V}
        </button>
      </td>
    `,c=t.comparison,h={kwh:q`<td>${_e(r,t.kwh)}</td>`,m3:q`<td>${ye(r,t.m3)}</td>`,kwh_invoice:q`<td>${_e(r,c?.invoice_kwh??t.kwh)}</td>`,kwh_edata:q`<td>${_e(r,c?.edata_kwh??null)}</td>`,delta_kwh:q`<td style=${l}>
        ${$e(r,c?.delta_kwh??null,"kwh")}
      </td>`,amount:q`<td>${me(r,t.total)}</td>`,delta_eur:q`<td style=${o}>
        ${$e(r,c?.delta_eur??null,"eur")}
      </td>`,price_kwh:q`<td>${ge(r,t.price_kwh)}</td>`},p=this._visible("gas"===t.supply?"gas":"electricity").map(e=>h[e.id]);return q`
      <tr class="row ${t.estimated?"estimated":""}" @click=${()=>this._toggle(s)}>
        ${d} ${p}
      </tr>
      ${a?q`<tr class="detail">
            <td colspan=${i}>${this._renderDetail(t)}</td>
          </tr>`:V}
    `}_renderDetail(e){const t=xe(this.hass),i="gas"!==e.supply,r=e.comparison;return q`
      <div class="detail-body">
        <ul>
          ${e.concepts.map(e=>q`<li><span>${e.label}</span><span>${me(t,e.amount)}</span></li>`)}
        </ul>
        <div>
          ${we(this.hass,"detail_vat",{rate:fe(t,e.vat.rate),base:me(t,e.vat.base),amount:me(t,e.vat.amount)})}
        </div>
        ${i?this._renderElectricityDetail(e,r):V}
        ${e.meter?this._renderMeterDetail(e.meter):V}
        ${e.in_group_of?q`<div>
              ${we(this.hass,"detail_in_group_of",{number:e.in_group_of})}
            </div>`:V}
        ${r&&r.group.length>1?q`<div>
              ${we(this.hass,"detail_group",{numbers:r.group.join(", ")})}
            </div>`:V}
      </div>
    `}_renderElectricityDetail(e,t){const i=xe(this.hass),r=t?.invoice_periods??e.periods,s=t?.edata_periods??null,a=null!==r||null!==s,n=(t?.group.length??0)>1;return q`
      ${n?q`<div>${we(this.hass,"detail_own_kwh",{kwh:_e(i,e.kwh)})}</div>
            <strong>
              ${we(this.hass,"detail_group_heading",{n:t?.group.length??0})}
            </strong>`:V}
      ${a?q`<ul>
            ${Ce.map(({key:e,name:t})=>q`<li>
                  ${we(this.hass,"detail_period_row",{period:t,invoice:_e(i,r?.[e]??null),edata:_e(i,s?.[e]??null)})}
                </li>`)}
          </ul>`:V}
      ${t?q`<div>
            ${we(this.hass,"detail_power_energy",{invoice:me(i,t.invoice_eur),edata:me(i,t.edata_eur)})}
            (${we(this.hass,"detail_delta_pct",{pct:ve(i,t.delta_pct)})})
          </div>`:V}
      <div>
        ${we(this.hass,"detail_energy_price",{price:ge(i,e.energy_price_kwh)})}
      </div>
    `}_toggle(e){const t=new Set(this._expanded);t.delete(e)||t.add(e),this._expanded=t}_selectSupply(e){e!==this.supply&&(this.supply=e,this._expanded=new Set,this.dispatchEvent(new CustomEvent("supply-changed",{detail:{supply:e},bubbles:!0,composed:!0})))}}function Ne(e){return Object.fromEntries(Object.entries(e).filter(([,e])=>void 0!==e))}function Ue(e,t={}){return e.connection.sendMessagePromise(Ne({type:"curenergia/invoices",entry_id:t.entry_id,supply:t.supply}))}function Ie(e,t){return e.connection.sendMessagePromise(Ne({type:"curenergia/summary",entry_id:t}))}Me.properties={hass:{attribute:!1},contracts:{attribute:!1},supply:{type:String},maxInvoices:{type:Number,attribute:"max-invoices"},columns:{attribute:!1},_expanded:{state:!0}},Me.styles=a`
    :host {
      display: block;
      color: var(--primary-text-color);
    }
    .tabs {
      display: flex;
      gap: 4px;
      border-bottom: 1px solid var(--divider-color);
      margin-bottom: 8px;
    }
    .tab {
      appearance: none;
      background: none;
      border: none;
      border-bottom: 2px solid transparent;
      color: var(--secondary-text-color);
      cursor: pointer;
      font: inherit;
      padding: 8px 12px;
    }
    .tab[aria-selected="true"] {
      border-bottom-color: var(--primary-color);
      color: var(--primary-text-color);
      font-weight: 500;
    }
    .contract-name {
      color: var(--secondary-text-color);
      font-size: 1em;
      font-weight: 500;
      margin: 12px 0 4px;
    }
    .scroll {
      overflow-x: auto;
    }
    table {
      border-collapse: collapse;
      width: 100%;
    }
    th,
    td {
      padding: 8px 6px;
      text-align: right;
      white-space: nowrap;
    }
    th:first-child,
    td:first-child {
      text-align: left;
    }
    th {
      border-bottom: 1px solid var(--divider-color);
      color: var(--secondary-text-color);
      font-weight: 500;
    }
    tr.row {
      cursor: pointer;
    }
    tr.row:hover,
    tr.row:focus-within {
      background: var(--secondary-background-color, transparent);
    }
    .toggle {
      appearance: none;
      background: none;
      border: none;
      color: inherit;
      cursor: pointer;
      font: inherit;
      margin: 0;
      padding: 0;
      text-align: left;
    }
    .toggle:focus-visible {
      outline: 2px solid var(--primary-color);
      outline-offset: 2px;
    }
    tr.row td {
      border-bottom: 1px solid var(--divider-color);
    }
    tr.row.estimated {
      color: var(--secondary-text-color);
    }
    /* Period with no stored invoice: muted, dashed, never clickable. */
    tr.gap td {
      border-bottom: 1px dashed var(--divider-color);
      color: var(--secondary-text-color);
      font-style: italic;
      text-align: left;
      white-space: normal;
    }
    .gap-hint {
      font-size: 0.85em;
      margin-left: 6px;
    }
    .pill {
      border: 1px solid var(--divider-color);
      border-radius: 10px;
      color: var(--secondary-text-color);
      font-size: 0.8em;
      margin-left: 6px;
      padding: 1px 6px;
    }
    .pill.error {
      border-color: var(--error-color);
      color: var(--error-color);
    }
    .note {
      color: var(--secondary-text-color);
      display: block;
      font-size: 0.85em;
    }
    tr.detail td {
      background: var(--secondary-background-color, transparent);
      border-bottom: 1px solid var(--divider-color);
      text-align: left;
      white-space: normal;
    }
    .detail-body {
      display: grid;
      gap: 6px;
      padding: 4px 0;
    }
    .detail-body ul {
      list-style: none;
      margin: 0;
      padding: 0;
    }
    .detail-body li {
      display: flex;
      gap: 12px;
      justify-content: space-between;
    }
    .empty {
      color: var(--secondary-text-color);
      padding: 16px 0;
      text-align: center;
    }
    .meter {
      border: 1px solid var(--divider-color);
      border-radius: var(--ha-card-border-radius, 12px);
      margin-bottom: 8px;
      padding: 10px 12px;
    }
    .meter-note {
      color: var(--secondary-text-color);
      font-size: 0.9em;
    }
    .meter-value {
      font-size: 1.6em;
      font-weight: 500;
    }
    .meter-periods {
      display: grid;
      gap: 8px;
      grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
      margin-top: 4px;
    }
    .meter-periods strong {
      display: block;
      font-weight: 500;
    }
    @media (max-width: 450px) {
      th,
      td {
        padding: 6px 4px;
      }
    }
  `,customElements.get("curenergia-invoice-table")||customElements.define("curenergia-invoice-table",Me);const Oe={columns_electricity:"electricity",columns_gas:"gas"},He={title:"editor_title",supply:"editor_supply",max_invoices:"editor_max_invoices",entry_id:"editor_entry_id",columns_electricity:"editor_columns_electricity",columns_gas:"editor_columns_gas"};class Te extends le{constructor(){super(),this._requestId=0,this._onSupplyChanged=e=>{const t=e.detail?.supply;"electricity"!==t&&"gas"!==t||(this._supply=t)},this._failed=!1,this._supply="electricity"}static getStubConfig(){return{max_invoices:6}}static getConfigForm(){const e=document.documentElement.lang||navigator.language||"en",t=t=>({select:{multiple:!0,mode:"list",options:Ee[t].map(t=>({value:t.id,label:ke(e,t.label)}))}});return{schema:[{name:"title",selector:{text:{}}},{name:"supply",selector:{select:{mode:"dropdown",options:[{value:"electricity",label:ke(e,"tab_electricity")},{value:"gas",label:ke(e,"tab_gas")}]}}},{name:"max_invoices",selector:{number:{min:1,max:60,mode:"box"}}},{name:"entry_id",selector:{config_entry:{integration:"curenergia"}}},{name:"columns_electricity",selector:t("electricity")},{name:"columns_gas",selector:t("gas")}],computeLabel:t=>{const i=He[t.name];return i?ke(e,i):void 0}}}get hass(){return this._hass}set hass(e){this._hass=e,this.requestUpdate(),this._start()}setConfig(e){const t=function(e){if(null===e||"object"!=typeof e||Array.isArray(e))throw new Error("Invalid configuration");const t=Object.fromEntries(Object.entries(e).filter(([,e])=>""!==e)),{max_invoices:i,supply:r,title:s,entry_id:a}=t;if(void 0!==i&&("number"!=typeof i||!Number.isInteger(i)||i<1||i>60))throw new Error("max_invoices must be an integer between 1 and 60");if(void 0!==r&&"electricity"!==r&&"gas"!==r)throw new Error('supply must be "electricity" or "gas"');if(void 0!==s&&"string"!=typeof s)throw new Error("title must be a string");if(void 0!==a&&"string"!=typeof a)throw new Error("entry_id must be a string");for(const[e,i]of Object.entries(Oe)){const r=t[e];if(void 0===r)continue;const s=Ee[i].map(e=>e.id);if(!Array.isArray(r)||r.some(e=>!s.includes(e)))throw new Error(`${e} must be a list with any of: ${s.join(", ")}`)}return t}(e),i=this._config;this._config=t,this._supply=t.supply??"electricity",i&&i.entry_id!==t.entry_id&&void 0!==this._timer&&this._load()}getCardSize(){const e=this._config?.max_invoices??6,t=(this._data??[]).filter(e=>e.supply===this._supply).reduce((e,t)=>e+t.invoices.length,0);return 3+Math.min(e,t)}connectedCallback(){super.connectedCallback(),this._start()}disconnectedCallback(){super.disconnectedCallback(),this._stop()}_start(){void 0===this._timer&&this.isConnected&&this._hass&&this._config&&(this._timer=setInterval(()=>{this._load()},9e5),this._load())}_stop(){void 0!==this._timer&&clearInterval(this._timer),this._timer=void 0,this._requestId+=1}async _load(){const e=this._hass;if(!e)return;this._requestId+=1;const t=this._requestId;try{const i=await Ue(e,{entry_id:this._config?.entry_id});if(t!==this._requestId)return;this._data=i.contracts??[],this._failed=!1}catch{if(t!==this._requestId)return;this._failed=!0}}render(){const e=this._config,t=this._hass;return e&&t?q`
      <ha-card .header=${e.title??we(t,"card_title")}>
        <div class="body">
          ${this._failed?q`<div class="message error">${we(t,"error")}</div>`:V}
          ${void 0===this._data?this._failed?V:q`<div class="message">${we(t,"loading")}</div>`:q`<curenergia-invoice-table
                .hass=${t}
                .contracts=${this._data}
                .supply=${this._supply}
                .maxInvoices=${e.max_invoices??6}
                .columns=${{electricity:e.columns_electricity,gas:e.columns_gas}}
                @supply-changed=${this._onSupplyChanged}
              ></curenergia-invoice-table>`}
        </div>
      </ha-card>
    `:V}}Te.properties={_config:{state:!0},_data:{state:!0},_failed:{state:!0},_supply:{state:!0}},Te.styles=a`
    :host {
      display: block;
    }
    ha-card {
      display: block;
    }
    .body {
      padding: 0 16px 16px;
    }
    .message {
      padding: 8px 0;
      color: var(--secondary-text-color);
    }
    .message.error {
      color: var(--error-color);
    }
  `,customElements.get("curenergia-invoices-card")||customElements.define("curenergia-invoices-card",Te);const De=window.customCards??=[];De.some(e=>"curenergia-invoices-card"===e.type)||De.push({type:"curenergia-invoices-card",name:"CurEnergía",description:be.en.card_description,preview:!1,documentationURL:"https://github.com/yuuues/hacs-curenergia#readme"});const Re=640,ze=212;function We(e,t){const i=/^(\d{4})-(\d{2})-(\d{2})/.exec(e);if(!i)return e;const r=`${i[3]}/${i[2]}`;return t?`${r}/${i[1].slice(2)}`:r}function je(e,t){const i=e.comparison;if(!i||null===i.edata_kwh)return null;if(i.group.length<=1)return i.edata_kwh;const r=t.filter(t=>t.in_group_of===e.number),s=i.group.filter(t=>t!==e.number);let a=i.edata_kwh;for(const e of s){const t=r.find(t=>t.number===e),i=t?.comparison?.edata_kwh??null;if(null===i)return null;a-=i}return Math.round(100*a)/100}function Le(e){return"no_leida"===e.status?"unreadable":e.estimated?"estimated":null}function qe(e,t){return e.period_end.localeCompare(t.period_end)||e.issue_date.localeCompare(t.issue_date)||e.number.localeCompare(t.number)}class Be extends le{constructor(){super(),this.invoices=[]}_points(){const e=this.invoices.filter(e=>"electricity"===e.supply),t=[...e].sort(qe).slice(-12),i=new Set(t.map(e=>e.period_end.slice(0,4))).size>1;return t.map(t=>({label:We(t.period_end,i),period:ue(t.period_start,t.period_end),invoice:t.kwh,datadis:je(t,e),mark:Le(t)}))}render(){const e=this.hass;if(!e)return V;const t=xe(e),i=this._points(),r=i.flatMap(e=>[e.invoice,e.datadis].filter(e=>null!==e));if(0===r.length)return q`<div class="message">${we(e,"chart_empty")}</div>`;const s=Math.max(...r,0),a=568/i.length,n=Math.min(.36*a,26),o=we(e,"chart_invoice"),l=we(e,"chart_datadis"),d=(i,r,a,d)=>{const c=(e=>s>0?Math.max(e,0)/s*196:0)(a),h="invoice"===i?o:l,p="invoice"===i?d.mark:null;return B`<rect
        class="bar ${i} ${p??""}"
        x=${r}
        y=${ze-c}
        width=${n}
        height=${c}
        rx="2"
      ><title>${h} ${d.period}: ${_e(t,a)}${(t=>"estimated"===t?` (${we(e,"pill_estimated")})`:"unreadable"===t?` (${we(e,"pill_unreadable")})`:"")(p)}</title></rect>`},c=new Set(i.map(e=>e.mark));return q`
      <div class="title">${we(e,"chart_title")}</div>
      <svg
        viewBox="0 0 ${Re} ${236}"
        role="img"
        aria-label=${we(e,"chart_title")}
        preserveAspectRatio="xMidYMid meet"
      >
        <line class="grid" x1=${64} x2=${632} y1=${16} y2=${16} />
        <line
          class="axis"
          x1=${64}
          x2=${632}
          y1=${ze}
          y2=${ze}
        />
        <text class="y-label" x=${58} y=${20} text-anchor="end">${_e(t,s)}</text>
        ${i.map((e,t)=>{const i=64+a*t+a/2,r=null!==e.invoice&&null!==e.datadis;return B`
            ${null!==e.invoice?d("invoice",r?i-n-1:i-n/2,e.invoice,e):V}
            ${null!==e.datadis?d("datadis",null!==e.invoice?i+1:i-n/2,e.datadis,e):V}
            <text class="x-label" x=${i} y=${228} text-anchor="middle">${e.label}</text>
          `})}
      </svg>
      <div class="legend">
        <span><i class="swatch invoice"></i>${o}</span>
        <span><i class="swatch datadis"></i>${l}</span>
        ${c.has("estimated")?q`<span><i class="swatch invoice estimated"></i>${we(e,"pill_estimated")}</span>`:V}
        ${c.has("unreadable")?q`<span><i class="swatch invoice unreadable"></i>${we(e,"pill_unreadable")}</span>`:V}
      </div>
    `}}Be.properties={hass:{attribute:!1},invoices:{attribute:!1}},Be.styles=a`
    :host {
      display: block;
      color: var(--primary-text-color);
    }
    .title {
      font-weight: 500;
      margin: 8px 0;
    }
    .message {
      padding: 8px 0;
      color: var(--secondary-text-color);
    }
    svg {
      display: block;
      width: 100%;
      height: auto;
    }
    .axis {
      stroke: var(--divider-color);
      stroke-width: 1;
    }
    .grid {
      stroke: var(--divider-color);
      stroke-width: 1;
      stroke-dasharray: 3 3;
    }
    text {
      fill: var(--secondary-text-color);
      font-size: 11px;
    }
    .bar.invoice {
      fill: var(--primary-color);
    }
    .bar.datadis {
      fill: var(--secondary-text-color);
    }
    /* Estimated or unreadable invoice figure: lighter fill and dashed outline. */
    .bar.invoice.estimated,
    .bar.invoice.unreadable {
      fill-opacity: 0.35;
      stroke: var(--primary-color);
      stroke-width: 1.5;
      stroke-dasharray: 3 2;
    }
    .bar.invoice.unreadable {
      stroke: var(--error-color);
    }
    .legend {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      margin: 4px 0 8px;
      color: var(--secondary-text-color);
      font-size: 0.9em;
    }
    .legend span {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .swatch {
      display: inline-block;
      width: 12px;
      height: 12px;
      border-radius: 2px;
    }
    .swatch.invoice {
      background: var(--primary-color);
    }
    .swatch.datadis {
      background: var(--secondary-text-color);
    }
    .swatch.invoice.estimated,
    .swatch.invoice.unreadable {
      background: transparent;
      border: 1.5px dashed var(--primary-color);
      box-sizing: border-box;
    }
    .swatch.invoice.unreadable {
      border-color: var(--error-color);
    }
  `,customElements.get("curenergia-bar-chart")||customElements.define("curenergia-bar-chart",Be);class Fe extends le{constructor(){super(),this._requestId=0,this._inFlight=!1,this._onSupplyChanged=e=>{const t=e.detail?.supply;"electricity"!==t&&"gas"!==t||(this._supply=t)},this._toggleMenu=()=>{this.dispatchEvent(new CustomEvent("hass-toggle-menu",{bubbles:!0,composed:!0}))},this.narrow=!1,this._failed=!1,this._supply="electricity"}get hass(){return this._hass}set hass(e){this._hass=e,this.requestUpdate(),this._start()}connectedCallback(){super.connectedCallback(),this._start()}disconnectedCallback(){super.disconnectedCallback(),this._stop()}_start(){void 0===this._timer&&this.isConnected&&this._hass&&(this._timer=setInterval(()=>{this._load()},9e5),this._load())}_stop(){void 0!==this._timer&&clearInterval(this._timer),this._timer=void 0,this._requestId+=1,this._inFlight=!1}async _load(){const e=this._hass;if(!e||this._inFlight)return;this._inFlight=!0,this._requestId+=1;const t=this._requestId;try{const[i,r]=await Promise.all([Ie(e),Ue(e)]);if(t!==this._requestId)return;this._summary=i,this._data=r.contracts??[],this._failed=!1}catch{if(t!==this._requestId)return;this._failed=!0}finally{t===this._requestId&&(this._inFlight=!1)}}_renderMenuButton(e){return customElements.get("ha-menu-button")?q`<ha-menu-button .hass=${e} .narrow=${this.narrow}></ha-menu-button>`:this.narrow?q`<button
      class="menu"
      type="button"
      aria-label=${we(e,"panel_menu")}
      @click=${this._toggleMenu}
    >
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z" />
      </svg>
    </button>`:V}_renderKpis(e){const t=xe(e),i=this._summary,r=(e,t)=>q`<div class="kpi">
        <div class="value">${t}</div>
        <div class="label">${e}</div>
      </div>`;return q`<div class="kpis">
      ${r(we(e,"panel_billed_12m"),me(t,i?.billed_12m??null))}
      ${r(we(e,"panel_kwh_delta"),function(e,t){if(null===t)return ce;const i=he(e,Math.abs(t),1,1);return`${0===Number(Math.abs(t).toFixed(1))?"":t<0?"−":"+"}${i} %`}(t,i?.kwh_delta_pct??null))}
      ${r(we(e,"panel_estimated_count"),i?function(e,t){return he(e,t,0,0)}(t,i.estimated_count):"—")}
    </div>`}_renderBody(e){if(void 0===this._data)return this._failed?q``:q`<div class="message">${we(e,"loading")}</div>`;if(0===this._data.length)return q`<div class="message">${we(e,"empty")}</div>`;const t=this._data.filter(e=>"electricity"===e.supply),i=t.length>1;return q`
      ${t.map(t=>q`
          <div class="section">
            ${i?q`<h3 class="chart-name">${t.name}</h3>`:V}
            <curenergia-bar-chart
              .hass=${e}
              .invoices=${t.invoices}
            ></curenergia-bar-chart>
          </div>
        `)}
      <div class="section">
        <curenergia-invoice-table
          .hass=${e}
          .contracts=${this._data}
          .supply=${this._supply}
          @supply-changed=${this._onSupplyChanged}
        ></curenergia-invoice-table>
      </div>
    `}render(){const e=this._hass;if(!e)return V;const t=this._summary;return q`
      <div class="toolbar">
        ${this._renderMenuButton(e)}
        <div class="title">${we(e,"panel_title")}</div>
      </div>
      <div class="content">
        ${this._failed?q`<div class="message error">${we(e,"error")}</div>`:V}
        ${this._renderKpis(e)}
        ${t?.mail_error?q`<div class="warning">${we(e,"panel_mail_error")}</div>`:V}
        ${t&&t.unreadable_emails>0?q`<div class="warning">
              ${we(e,"panel_unreadable",{n:t.unreadable_emails})}
            </div>`:V}
        ${t&&t.unsupported_emails>0?q`<div class="warning">
              ${we(e,"panel_unsupported",{n:t.unsupported_emails})}
            </div>`:V}
        ${this._renderBody(e)}
      </div>
    `}}Fe.properties={hass:{attribute:!1},narrow:{type:Boolean},panel:{attribute:!1},_data:{state:!0},_summary:{state:!0},_failed:{state:!0},_supply:{state:!0}},Fe.styles=a`
    :host {
      display: block;
      min-height: 100%;
      background: var(--primary-background-color);
      color: var(--primary-text-color);
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 8px;
      height: calc(56px + env(safe-area-inset-top, 0px));
      padding: 0 12px;
      padding-top: env(safe-area-inset-top, 0px);
      box-sizing: border-box;
      background: var(--app-header-background-color);
      color: var(--app-header-text-color, var(--primary-text-color));
    }
    .menu {
      appearance: none;
      background: none;
      border: none;
      border-radius: 50%;
      color: inherit;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 48px;
      height: 48px;
      padding: 12px;
      box-sizing: border-box;
    }
    .menu:focus-visible {
      outline: 2px solid var(--primary-color);
    }
    .menu svg {
      width: 24px;
      height: 24px;
      fill: currentColor;
    }
    .toolbar .title {
      font-size: 20px;
      font-weight: 400;
    }
    .content {
      max-width: 1100px;
      margin: 0 auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .kpis {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
    }
    .kpi,
    .section {
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
      border-radius: var(--ha-card-border-radius, 12px);
      padding: 16px;
    }
    .kpi .value {
      font-size: 1.8em;
      font-weight: 500;
    }
    .kpi .label {
      margin-top: 4px;
      color: var(--secondary-text-color);
    }
    .warning {
      padding: 8px 12px;
      border-left: 4px solid var(--warning-color);
      background: var(--card-background-color);
      border-radius: 4px;
    }
    .chart-name {
      color: var(--secondary-text-color);
      font-size: 1em;
      font-weight: 500;
      margin: 0 0 4px;
    }
    .message {
      padding: 8px 0;
      color: var(--secondary-text-color);
    }
    .message.error {
      color: var(--error-color);
    }
  `,customElements.get("curenergia-panel")||customElements.define("curenergia-panel",Fe);
